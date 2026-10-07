import uuid
import io
import pandas as pd
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.project import Project
from app.models.public_work import PublicMpladsWork
from app.schemas.ingestion import (
    IngestionPreviewResponse,
    IngestionCommitRequest,
    IngestionCommitResponse
)
from app.services.ingestion_service import (
    process_and_clean_file,
    process_and_clean_public_file,
    parse_currency,
    parse_date
)

router = APIRouter(prefix="/api/ingestion", tags=["Data Ingestion"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_PUBLIC_FILE_SIZE_BYTES = 50 * 1024 * 1024     # 50 MB
MAX_CONTROLLED_FILE_SIZE_BYTES = 10 * 1024 * 1024 # 10 MB

@router.post("/preview", response_model=IngestionPreviewResponse)
async def preview_ingestion(
    dataset_type: Optional[str] = Query(None, description="CONTROLLED_TEST or PUBLIC_MPLADS_DERIVED"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Parses and cleans an uploaded CSV/XLSX file based on dataset mode.
    Does NOT write to database. Returns metrics, preview rows (max 50), and validation issues.
    """
    filename = file.filename or "uploaded_data.csv"
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Accepts .csv and .xlsx files only."
        )

    file_bytes = await file.read()
    
    # Check limit based on target or auto-detected dataset_type
    target_mode = dataset_type or "CONTROLLED_TEST"
    if target_mode == "PUBLIC_MPLADS_DERIVED" and len(file_bytes) > MAX_PUBLIC_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50 MB limit for Public MPLADS dataset."
        )
    elif target_mode == "CONTROLLED_TEST" and len(file_bytes) > MAX_CONTROLLED_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10 MB limit for Controlled Test dataset."
        )

    # Auto-detect dataset mode if not explicitly passed
    if not dataset_type:
        try:
            if filename.endswith(".csv"):
                df_head = pd.read_csv(io.BytesIO(file_bytes), nrows=5)
            else:
                df_head = pd.read_excel(io.BytesIO(file_bytes), nrows=5)
            
            headers = set(str(c).strip().lower() for c in df_head.columns)
            if "internal_record_key" in headers or "recommended_amount" in headers or "mp_name" in headers:
                dataset_type = "PUBLIC_MPLADS_DERIVED"
            else:
                dataset_type = "CONTROLLED_TEST"
        except Exception:
            dataset_type = "CONTROLLED_TEST"

        # Re-check size limit if auto-detected as PUBLIC_MPLADS_DERIVED
        if dataset_type == "PUBLIC_MPLADS_DERIVED" and len(file_bytes) > MAX_PUBLIC_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 50 MB limit for Public MPLADS dataset."
            )

    try:
        if dataset_type == "PUBLIC_MPLADS_DERIVED":
            preview_result = process_and_clean_public_file(file_bytes, filename, db)
        else:
            preview_result = process_and_clean_file(file_bytes, filename, db)
            
        return preview_result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )

@router.post("/commit", response_model=IngestionCommitResponse)
async def commit_ingestion(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Commits validated clean records into database based on dataset_type.
    Supports JSON payload or multipart/form-data file upload.
    Commits records in batches of 1,000.
    """
    batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    content_type = request.headers.get("content-type", "")

    inserted_count = 0
    skipped_duplicates = 0
    rejected_count = 0

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        uploaded_file: Optional[UploadFile] = form.get("file")
        dataset_type = form.get("dataset_type", "PUBLIC_MPLADS_DERIVED")
        data_source = form.get("data_source", "PUBLIC_MPLADS_DERIVED_GITHUB")

        if not uploaded_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided for database commit."
            )

        file_bytes = await uploaded_file.read()
        filename = uploaded_file.filename or "data.csv"

        if dataset_type == "PUBLIC_MPLADS_DERIVED":
            if len(file_bytes) > MAX_PUBLIC_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size exceeds 50 MB limit for Public MPLADS dataset."
                )
            
            existing_keys = set(w.internal_record_key for w in db.query(PublicMpladsWork.internal_record_key).all())
            works_to_insert = []

            chunk_iter = pd.read_csv(io.BytesIO(file_bytes), chunksize=5000) if filename.endswith(".csv") else [pd.read_excel(io.BytesIO(file_bytes))]
            
            rows_processed = 0
            for chunk in chunk_iter:
                for idx, row in chunk.iterrows():
                    rows_processed += 1
                    raw_key = row.get("internal_record_key", None)
                    r_key = str(raw_key).strip() if (not pd.isna(raw_key) and raw_key is not None and str(raw_key).strip() != "") else None

                    if not r_key:
                        rejected_count += 1
                        continue

                    raw_dup = row.get("exact_source_duplicate", False)
                    is_source_dup = str(raw_dup).strip().lower() in ("true", "1", "t", "yes")

                    if r_key in existing_keys or is_source_dup:
                        skipped_duplicates += 1
                        continue

                    rec_amt, rec_amt_ok = parse_currency(row.get("recommended_amount", None))
                    if not rec_amt_ok or rec_amt < 0:
                        rejected_count += 1
                        continue

                    rec_date_str, _ = parse_date(row.get("recommended_date", None))
                    rec_date = None
                    if rec_date_str:
                        try:
                            rec_date = datetime.strptime(rec_date_str, "%Y-%m-%d").date()
                        except Exception:
                            rec_date = None

                    w_desc = row.get("work_description", None)
                    n_work = row.get("normalized_work", None)
                    work_str = str(w_desc).strip() if (not pd.isna(w_desc) and str(w_desc).strip() != "" and str(w_desc).strip().upper() != "NA") else (str(n_work).strip() if not pd.isna(n_work) else "")

                    new_work = PublicMpladsWork(
                        internal_record_key=r_key,
                        mp_name=str(row.get("mp_name", "")).strip() if not pd.isna(row.get("mp_name", None)) else None,
                        work_description=str(w_desc).strip() if not pd.isna(w_desc) else None,
                        normalized_work=str(n_work).strip() if not pd.isna(n_work) else work_str,
                        source_category=str(row.get("source_category", "")).strip() if not pd.isna(row.get("source_category", None)) else None,
                        state=str(row.get("state", "")).strip() if not pd.isna(row.get("state", None)) else None,
                        constituency=str(row.get("constituency", "")).strip() if not pd.isna(row.get("constituency", None)) else None,
                        implementing_district_authority=str(row.get("implementing_district_authority", "")).strip() if not pd.isna(row.get("implementing_district_authority", None)) else None,
                        city=str(row.get("city", "")).strip() if not pd.isna(row.get("city", None)) else None,
                        ward=str(row.get("ward", "")).strip() if not pd.isna(row.get("ward", None)) else None,
                        block=str(row.get("block", "")).strip() if not pd.isna(row.get("block", None)) else None,
                        village=str(row.get("village", "")).strip() if not pd.isna(row.get("village", None)) else None,
                        location_text=str(row.get("location_text", "")).strip() if not pd.isna(row.get("location_text", None)) else None,
                        recommended_date=rec_date,
                        recommended_amount=rec_amt,
                        ida_approval_status=str(row.get("ida_approval_status", "")).strip() if not pd.isna(row.get("ida_approval_status", None)) else "Pending",
                        work_status=str(row.get("work_status", "")).strip() if not pd.isna(row.get("work_status", None)) else "Unsanctioned",
                        house=str(row.get("house", "")).strip() if not pd.isna(row.get("house", None)) else None,
                        exact_source_duplicate=is_source_dup,
                        source_row_number=rows_processed,
                        data_quality_status=str(row.get("data_quality_status", "COMPLETE")).strip() if not pd.isna(row.get("data_quality_status", None)) else "COMPLETE",
                        data_source=data_source or "PUBLIC_MPLADS_DERIVED",
                        import_batch_id=batch_id
                    )

                    works_to_insert.append(new_work)
                    existing_keys.add(r_key)

                    # Commit records in batches of 1,000
                    if len(works_to_insert) >= 1000:
                        db.add_all(works_to_insert)
                        db.commit()
                        inserted_count += len(works_to_insert)
                        works_to_insert.clear()

            if works_to_insert:
                db.add_all(works_to_insert)
                db.commit()
                inserted_count += len(works_to_insert)
                works_to_insert.clear()

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Multipart commit is supported for PUBLIC_MPLADS_DERIVED datasets."
            )

    else:
        # Standard JSON body commit payload
        try:
            json_body = await request.json()
            payload = IngestionCommitRequest(**json_body)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON structure in request: {str(e)}"
            )

        if not payload.records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No records provided for database commit."
            )

        dataset_type = payload.dataset_type or "CONTROLLED_TEST"

        if dataset_type == "PUBLIC_MPLADS_DERIVED":
            existing_keys = set(w.internal_record_key for w in db.query(PublicMpladsWork.internal_record_key).all())
            works_to_insert = []

            for item in payload.records:
                row_status = item.get("status", "VALID")
                data = item.get("data", item)

                if row_status == "REJECTED":
                    rejected_count += 1
                    continue

                r_key = data.get("internal_record_key")
                if not r_key or r_key in existing_keys:
                    skipped_duplicates += 1
                    continue

                rec_date = None
                if data.get("recommended_date"):
                    try:
                        rec_date = datetime.strptime(data["recommended_date"], "%Y-%m-%d").date() if isinstance(data["recommended_date"], str) else data["recommended_date"]
                    except Exception:
                        rec_date = None

                new_work = PublicMpladsWork(
                    internal_record_key=r_key,
                    mp_name=data.get("mp_name"),
                    work_description=data.get("work_description"),
                    normalized_work=data.get("normalized_work"),
                    source_category=data.get("source_category"),
                    state=data.get("state"),
                    constituency=data.get("constituency"),
                    implementing_district_authority=data.get("implementing_district_authority"),
                    city=data.get("city"),
                    ward=data.get("ward"),
                    block=data.get("block"),
                    village=data.get("village"),
                    location_text=data.get("location_text"),
                    recommended_date=rec_date,
                    recommended_amount=float(data.get("recommended_amount", 0.0)) if data.get("recommended_amount") else None,
                    ida_approval_status=data.get("ida_approval_status"),
                    work_status=data.get("work_status"),
                    house=data.get("house"),
                    exact_source_duplicate=bool(data.get("exact_source_duplicate", False)),
                    source_row_number=data.get("source_row_number"),
                    data_quality_status=data.get("data_quality_status", "COMPLETE"),
                    data_source=payload.data_source or "PUBLIC_MPLADS_DERIVED",
                    import_batch_id=batch_id
                )

                works_to_insert.append(new_work)
                existing_keys.add(r_key)

                # Commit in batches of 1,000
                if len(works_to_insert) >= 1000:
                    db.add_all(works_to_insert)
                    db.commit()
                    inserted_count += len(works_to_insert)
                    works_to_insert.clear()

            if works_to_insert:
                db.add_all(works_to_insert)
                db.commit()
                inserted_count += len(works_to_insert)
                works_to_insert.clear()

        else:
            # Controlled Test Dataset Commit
            existing_db_ids = set(p.project_id for p in db.query(Project.project_id).all())
            projects_to_insert = []

            for item in payload.records:
                row_status = item.get("status", "VALID")
                data = item.get("data", item)

                if row_status == "REJECTED":
                    rejected_count += 1
                    continue

                pid = data.get("project_id")
                if not pid or pid in existing_db_ids:
                    skipped_duplicates += 1
                    continue

                try:
                    s_date = datetime.strptime(data["sanction_date"], "%Y-%m-%d").date() if isinstance(data["sanction_date"], str) else data["sanction_date"]
                    exp_date = datetime.strptime(data["expected_completion_date"], "%Y-%m-%d").date() if isinstance(data["expected_completion_date"], str) else data["expected_completion_date"]
                    act_date = None
                    if data.get("actual_completion_date"):
                        act_date = datetime.strptime(data["actual_completion_date"], "%Y-%m-%d").date() if isinstance(data["actual_completion_date"], str) else data["actual_completion_date"]
                except Exception:
                    rejected_count += 1
                    continue

                new_project = Project(
                    project_id=pid,
                    project_name=data.get("project_name", ""),
                    district=data.get("district", ""),
                    project_type=data.get("project_type", ""),
                    sanctioned_amount=float(data.get("sanctioned_amount", 0.0)),
                    expenditure=float(data.get("expenditure", 0.0)),
                    sanction_date=s_date,
                    expected_completion_date=exp_date,
                    actual_completion_date=act_date,
                    progress_percent=float(data.get("progress_percent", 0.0)),
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                    status=data.get("status", "In Progress"),
                    supporting_document=data.get("supporting_document"),
                    data_source=payload.data_source or "CONTROLLED_TEST",
                    import_batch_id=batch_id,
                    audit_status=data.get("audit_status", "Not In Queue")
                )

                projects_to_insert.append(new_project)
                existing_db_ids.add(pid)

                # Commit in batches of 1,000
                if len(projects_to_insert) >= 1000:
                    db.add_all(projects_to_insert)
                    db.commit()
                    inserted_count += len(projects_to_insert)
                    projects_to_insert.clear()

            if projects_to_insert:
                db.add_all(projects_to_insert)
                db.commit()
                inserted_count += len(projects_to_insert)
                projects_to_insert.clear()

    return {
        "inserted": inserted_count,
        "skipped_duplicates": skipped_duplicates,
        "rejected": rejected_count,
        "batch_id": batch_id
    }

@router.get("/template")
def download_csv_template(dataset_type: str = Query("CONTROLLED_TEST")):
    """
    Returns a downloadable CSV template based on dataset_type.
    """
    if dataset_type == "PUBLIC_MPLADS_DERIVED":
        csv_header = (
            "internal_record_key,mp_name,work_description,normalized_work,source_category,state,constituency,"
            "implementing_district_authority,city,ward,block,village,location_text,recommended_date,recommended_amount,"
            "ida_approval_status,work_status,house,exact_source_duplicate,source_row_number,data_quality_status,data_source\n"
            "PUB-569417A2394CA144,TRVS Ramesh,NA - Lighting of public spaces,Lighting of public spaces,Normal/Others,Tamil Nadu,"
            "CUDDALORE,DISTRICT COLLECTOR CUDDALORE_IDA,,,Tittakudi,Pattur,Pattur | Tittakudi | CUDDALORE,2024-01-04,450000.0,"
            "Action Pending,Unsanctioned,Lok Sabha,False,10156,CORE_COMPLETE_LOCATION_PARTIAL,PUBLIC_MPLADS_DERIVED_GITHUB\n"
        )
        filename = "public_mplads_import_template.csv"
    else:
        csv_header = (
            "project_id,project_name,district,project_type,sanctioned_amount,"
            "expenditure,sanction_date,expected_completion_date,actual_completion_date,"
            "progress_percent,latitude,longitude,status,supporting_document\n"
            "ERD-ROAD-005,Construction of Rural Feeder Road at Modakurichi,Erode,Road,"
            "2000000,1950000,2025-10-10,2026-04-10,2026-04-05,100.0,11.2384,77.8188,Completed,ERD_ROAD_005_bill.pdf\n"
        )
        filename = "mplads_import_template.csv"

    return StreamingResponse(
        io.BytesIO(csv_header.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

