import re
import io
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from app.config.column_aliases import normalise_column_name
from app.models.project import Project
from app.models.public_work import PublicMpladsWork

REQUIRED_FIELDS = [
    "project_id",
    "project_name",
    "district",
    "project_type",
    "sanctioned_amount",
    "expenditure",
    "sanction_date",
    "expected_completion_date",
    "progress_percent",
    "status"
]

OPTIONAL_FIELDS = [
    "actual_completion_date",
    "latitude",
    "longitude",
    "supporting_document"
]

def parse_currency(val: Any) -> Tuple[float, bool]:
    """Cleans currency formatted string (e.g. ₹25,00,000.00) into float."""
    if pd.isna(val) or val is None or str(val).strip() == "":
        return 0.0, False
    
    val_str = str(val).replace("₹", "").replace(",", "").strip()
    try:
        amount = float(val_str)
        return amount, True
    except ValueError:
        return 0.0, False

def parse_date(val: Any) -> Tuple[str, bool]:
    """Parses various date string formats to YYYY-MM-DD string."""
    if pd.isna(val) or val is None or str(val).strip() == "":
        return None, True  # Empty date is valid for optional fields
    
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d"), True

    val_str = str(val).strip()
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d",
        "%d-%b-%Y", "%d %b %Y", "%b %d, %Y"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(val_str, fmt)
            return dt.strftime("%Y-%m-%d"), True
        except ValueError:
            continue
            
    try:
        dt = pd.to_datetime(val_str, dayfirst=True)
        if not pd.isna(dt):
            return dt.strftime("%Y-%m-%d"), True
    except Exception:
        pass

    return None, False

def process_and_clean_file(
    file_bytes: bytes, 
    filename: str, 
    db: Session
) -> Dict[str, Any]:
    """
    Parses Controlled Test CSV/XLSX file against the standard Project schema.
    """
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            raise ValueError("Unsupported file format. Please upload .csv or .xlsx file.")
    except Exception as e:
        raise ValueError(f"Failed to read file: {str(e)}")

    raw_columns = list(df.columns)
    column_mapping = {col: normalise_column_name(col) for col in raw_columns}
    df.rename(columns=column_mapping, inplace=True)

    existing_db_ids = set(p.project_id for p in db.query(Project.project_id).all())

    rows_received = len(df)
    clean_preview = []
    all_issues = []
    
    valid_count = 0
    warning_count = 0
    rejected_count = 0
    duplicate_count = 0
    missing_optional_count = 0
    seen_uploaded_ids = set()

    for idx, row in df.iterrows():
        row_num = idx + 1
        row_data = {}
        row_issues = []
        is_rejected = False
        has_warning = False

        raw_pid = row.get("project_id", None)
        project_id = str(raw_pid).strip() if (not pd.isna(raw_pid) and raw_pid is not None) else None

        if not project_id:
            is_rejected = True
            row_issues.append({
                "row_number": row_num,
                "project_id": None,
                "field": "project_id",
                "issue_type": "MISSING_FIELD",
                "message": "Required field 'project_id' is missing or empty."
            })
        else:
            row_data["project_id"] = project_id
            if project_id in seen_uploaded_ids or project_id in existing_db_ids:
                has_warning = True
                duplicate_count += 1
                row_issues.append({
                    "row_number": row_num,
                    "project_id": project_id,
                    "field": "project_id",
                    "issue_type": "DUPLICATE_ID",
                    "message": f"Project ID '{project_id}' already exists in database or current file."
                })
            seen_uploaded_ids.add(project_id)

        pname = row.get("project_name", None)
        if pd.isna(pname) or pname is None or str(pname).strip() == "":
            is_rejected = True
            row_issues.append({
                "row_number": row_num,
                "project_id": project_id,
                "field": "project_name",
                "issue_type": "MISSING_FIELD",
                "message": "Required field 'project_name' is missing."
            })
        else:
            row_data["project_name"] = str(pname).strip()

        dist = row.get("district", None)
        if pd.isna(dist) or dist is None or str(dist).strip() == "":
            is_rejected = True
            row_issues.append({
                "row_number": row_num,
                "project_id": project_id,
                "field": "district",
                "issue_type": "MISSING_FIELD",
                "message": "Required field 'district' is missing."
            })
        else:
            row_data["district"] = str(dist).strip().title()

        ptype = row.get("project_type", None)
        if pd.isna(ptype) or ptype is None or str(ptype).strip() == "":
            is_rejected = True
            row_issues.append({
                "row_number": row_num,
                "project_id": project_id,
                "field": "project_type",
                "issue_type": "MISSING_FIELD",
                "message": "Required field 'project_type' is missing."
            })
        else:
            row_data["project_type"] = str(ptype).strip().title()

        s_amt, s_ok = parse_currency(row.get("sanctioned_amount", None))
        if not s_ok or s_amt < 0:
            is_rejected = True
            row_issues.append({
                "row_number": row_num,
                "project_id": project_id,
                "field": "sanctioned_amount",
                "issue_type": "INVALID_VALUE",
                "message": "Sanctioned amount must be a non-negative number."
            })
        else:
            row_data["sanctioned_amount"] = s_amt

        e_amt, e_ok = parse_currency(row.get("expenditure", None))
        if not e_ok or e_amt < 0:
            is_rejected = True
            row_issues.append({
                "row_number": row_num,
                "project_id": project_id,
                "field": "expenditure",
                "issue_type": "INVALID_VALUE",
                "message": "Expenditure must be a non-negative number."
            })
        else:
            row_data["expenditure"] = e_amt

        s_date, s_dt_ok = parse_date(row.get("sanction_date", None))
        if not s_dt_ok or not s_date:
            is_rejected = True
            row_issues.append({
                "row_number": row_num,
                "project_id": project_id,
                "field": "sanction_date",
                "issue_type": "INVALID_VALUE",
                "message": "Sanction date is missing or unparseable."
            })
        else:
            row_data["sanction_date"] = s_date

        exp_date, exp_dt_ok = parse_date(row.get("expected_completion_date", None))
        if not exp_dt_ok or not exp_date:
            is_rejected = True
            row_issues.append({
                "row_number": row_num,
                "project_id": project_id,
                "field": "expected_completion_date",
                "issue_type": "INVALID_VALUE",
                "message": "Expected completion date is missing or unparseable."
            })
        else:
            row_data["expected_completion_date"] = exp_date

        act_raw = row.get("actual_completion_date", None)
        act_date, act_dt_ok = parse_date(act_raw)
        if not act_dt_ok:
            has_warning = True
            missing_optional_count += 1
            row_issues.append({
                "row_number": row_num,
                "project_id": project_id,
                "field": "actual_completion_date",
                "issue_type": "WARNING_MISSING_OPTIONAL",
                "message": "Actual completion date could not be parsed."
            })
            row_data["actual_completion_date"] = None
        else:
            row_data["actual_completion_date"] = act_date

        prog_raw = row.get("progress_percent", None)
        try:
            if pd.isna(prog_raw) or prog_raw is None or str(prog_raw).strip() == "":
                raise ValueError()
            prog_str = str(prog_raw).replace("%", "").strip()
            prog_val = float(prog_str)
            if prog_val < 0 or prog_val > 100:
                raise ValueError()
            row_data["progress_percent"] = prog_val
        except ValueError:
            is_rejected = True
            row_issues.append({
                "row_number": row_num,
                "project_id": project_id,
                "field": "progress_percent",
                "issue_type": "INVALID_VALUE",
                "message": "Progress percent must be a valid number between 0 and 100."
            })

        st_raw = row.get("status", None)
        if pd.isna(st_raw) or st_raw is None or str(st_raw).strip() == "":
            is_rejected = True
            row_issues.append({
                "row_number": row_num,
                "project_id": project_id,
                "field": "status",
                "issue_type": "MISSING_FIELD",
                "message": "Required field 'status' is missing."
            })
        else:
            row_data["status"] = str(st_raw).strip().title()

        lat_raw = row.get("latitude", None)
        row_data["latitude"] = None
        if not pd.isna(lat_raw) and lat_raw is not None and str(lat_raw).strip() != "":
            try:
                lat_val = float(str(lat_raw).strip())
                if -90 <= lat_val <= 90:
                    row_data["latitude"] = lat_val
                else:
                    has_warning = True
                    missing_optional_count += 1
                    row_issues.append({
                        "row_number": row_num,
                        "project_id": project_id,
                        "field": "latitude",
                        "issue_type": "WARNING_MISSING_OPTIONAL",
                        "message": "Latitude out of range [-90, 90]. Storing NULL."
                    })
            except ValueError:
                has_warning = True
                missing_optional_count += 1
                row_issues.append({
                    "row_number": row_num,
                    "project_id": project_id,
                    "field": "latitude",
                    "issue_type": "WARNING_MISSING_OPTIONAL",
                    "message": "Invalid latitude value. Storing NULL."
                })

        lng_raw = row.get("longitude", None)
        row_data["longitude"] = None
        if not pd.isna(lng_raw) and lng_raw is not None and str(lng_raw).strip() != "":
            try:
                lng_val = float(str(lng_raw).strip())
                if -180 <= lng_val <= 180:
                    row_data["longitude"] = lng_val
                else:
                    has_warning = True
                    missing_optional_count += 1
                    row_issues.append({
                        "row_number": row_num,
                        "project_id": project_id,
                        "field": "longitude",
                        "issue_type": "WARNING_MISSING_OPTIONAL",
                        "message": "Longitude out of range [-180, 180]. Storing NULL."
                    })
            except ValueError:
                has_warning = True
                missing_optional_count += 1
                row_issues.append({
                    "row_number": row_num,
                    "project_id": project_id,
                    "field": "longitude",
                    "issue_type": "WARNING_MISSING_OPTIONAL",
                    "message": "Invalid longitude value. Storing NULL."
                })

        doc_raw = row.get("supporting_document", None)
        row_data["supporting_document"] = str(doc_raw).strip() if (not pd.isna(doc_raw) and doc_raw is not None and str(doc_raw).strip() != "") else None

        if is_rejected:
            row_status = "REJECTED"
            rejected_count += 1
        elif has_warning:
            row_status = "WARNING"
            warning_count += 1
        else:
            row_status = "VALID"
            valid_count += 1

        clean_preview.append({
            "row_number": row_num,
            "status": row_status,
            "data": row_data,
            "issues": row_issues
        })

        all_issues.extend(row_issues)

    return {
        "dataset_type": "CONTROLLED_TEST",
        "filename": filename,
        "rows_received": rows_received,
        "valid_rows": valid_count,
        "warning_rows": warning_count,
        "rejected_rows": rejected_count,
        "duplicate_rows": duplicate_count,
        "missing_values": missing_optional_count,
        "clean_preview": clean_preview,
        "issues": all_issues
    }

def process_and_clean_public_file(
    file_bytes: bytes,
    filename: str,
    db: Session,
    chunksize: int = 5000
) -> Dict[str, Any]:
    """
    Parses Public MPLADS-Derived CSV/XLSX dataset using pandas chunksize streaming.
    Validates in chunks, aggregates overall metrics, and returns only first 50 preview rows.
    """
    try:
        if filename.endswith(".csv"):
            chunk_iter = pd.read_csv(io.BytesIO(file_bytes), chunksize=chunksize)
        elif filename.endswith((".xlsx", ".xls")):
            full_df = pd.read_excel(io.BytesIO(file_bytes))
            chunk_iter = [full_df[i:i + chunksize] for i in range(0, len(full_df), chunksize)]
        else:
            raise ValueError("Unsupported file format. Accepts .csv and .xlsx files only.")
    except pd.errors.EmptyDataError:
        raise ValueError("Invalid CSV structure: File is empty or unreadable.")
    except pd.errors.ParserError as pe:
        raise ValueError(f"Invalid CSV structure: Failed to parse CSV rows ({str(pe)}).")
    except Exception as e:
        if "Unsupported file format" in str(e):
            raise ValueError(str(e))
        raise ValueError(f"Invalid CSV structure: {str(e)}")

    existing_public_keys = set(w.internal_record_key for w in db.query(PublicMpladsWork.internal_record_key).all())

    rows_received = 0
    clean_preview = []
    all_issues = []

    valid_count = 0
    warning_count = 0
    rejected_count = 0
    duplicate_count = 0
    missing_optional_count = 0
    seen_uploaded_keys = set()

    for chunk in chunk_iter:
        if rows_received == 0:
            headers = set(str(c).strip().lower() for c in chunk.columns)
            if "internal_record_key" not in headers:
                raise ValueError("Unsupported schema: Public MPLADS dataset must contain 'internal_record_key' column.")

        for idx, row in chunk.iterrows():
            rows_received += 1
            row_num = rows_received
            row_data = {}
            row_issues = []
            is_rejected = False
            has_warning = False

            # Required key: internal_record_key
            raw_key = row.get("internal_record_key", None)
            record_key = str(raw_key).strip() if (not pd.isna(raw_key) and raw_key is not None and str(raw_key).strip() != "") else None

            if not record_key:
                is_rejected = True
                row_issues.append({
                    "row_number": row_num,
                    "project_id": None,
                    "field": "internal_record_key",
                    "issue_type": "MISSING_FIELD",
                    "message": "Required field 'internal_record_key' is missing."
                })
            else:
                row_data["internal_record_key"] = record_key

            # Exact source duplicate check
            raw_dup = row.get("exact_source_duplicate", False)
            is_source_dup = str(raw_dup).strip().lower() in ("true", "1", "t", "yes")
            row_data["exact_source_duplicate"] = is_source_dup

            if record_key and (record_key in seen_uploaded_keys or record_key in existing_public_keys or is_source_dup):
                has_warning = True
                duplicate_count += 1
                row_issues.append({
                    "row_number": row_num,
                    "project_id": record_key,
                    "field": "internal_record_key",
                    "issue_type": "DUPLICATE_ID",
                    "message": f"Record key '{record_key}' is an exact duplicate in dataset or database."
                })
            if record_key:
                seen_uploaded_keys.add(record_key)

            # Work description / normalized work
            w_desc = row.get("work_description", None)
            n_work = row.get("normalized_work", None)

            work_str = ""
            if not pd.isna(w_desc) and str(w_desc).strip() != "" and str(w_desc).strip().upper() != "NA":
                work_str = str(w_desc).strip()
            elif not pd.isna(n_work) and str(n_work).strip() != "":
                work_str = str(n_work).strip()

            if not work_str:
                has_warning = True
                missing_optional_count += 1
                row_issues.append({
                    "row_number": row_num,
                    "project_id": record_key,
                    "field": "work_description",
                    "issue_type": "WARNING_MISSING_OPTIONAL",
                    "message": "Work description is empty or unspecified."
                })

            row_data["work_description"] = str(w_desc).strip() if (not pd.isna(w_desc) and w_desc is not None) else None
            row_data["normalized_work"] = str(n_work).strip() if (not pd.isna(n_work) and n_work is not None) else work_str
            row_data["mp_name"] = str(row.get("mp_name", "")).strip() if not pd.isna(row.get("mp_name", None)) else None
            row_data["source_category"] = str(row.get("source_category", "")).strip() if not pd.isna(row.get("source_category", None)) else None
            row_data["state"] = str(row.get("state", "")).strip() if not pd.isna(row.get("state", None)) else None
            row_data["constituency"] = str(row.get("constituency", "")).strip() if not pd.isna(row.get("constituency", None)) else None
            row_data["implementing_district_authority"] = str(row.get("implementing_district_authority", "")).strip() if not pd.isna(row.get("implementing_district_authority", None)) else None
            row_data["city"] = str(row.get("city", "")).strip() if not pd.isna(row.get("city", None)) else None
            row_data["ward"] = str(row.get("ward", "")).strip() if not pd.isna(row.get("ward", None)) else None
            row_data["block"] = str(row.get("block", "")).strip() if not pd.isna(row.get("block", None)) else None
            row_data["village"] = str(row.get("village", "")).strip() if not pd.isna(row.get("village", None)) else None
            row_data["location_text"] = str(row.get("location_text", "")).strip() if not pd.isna(row.get("location_text", None)) else None

            # Recommended Date
            rec_date, rec_dt_ok = parse_date(row.get("recommended_date", None))
            if not rec_dt_ok:
                has_warning = True
                missing_optional_count += 1
                row_issues.append({
                    "row_number": row_num,
                    "project_id": record_key,
                    "field": "recommended_date",
                    "issue_type": "WARNING_MISSING_OPTIONAL",
                    "message": "Recommended date is missing or unparseable."
                })
                row_data["recommended_date"] = None
            else:
                row_data["recommended_date"] = rec_date

            # Recommended Amount
            rec_amt, rec_amt_ok = parse_currency(row.get("recommended_amount", None))
            if not rec_amt_ok or rec_amt < 0:
                is_rejected = True
                row_issues.append({
                    "row_number": row_num,
                    "project_id": record_key,
                    "field": "recommended_amount",
                    "issue_type": "INVALID_VALUE",
                    "message": "Recommended amount must be a valid non-negative number."
                })
                row_data["recommended_amount"] = 0.0
            else:
                row_data["recommended_amount"] = rec_amt

            row_data["ida_approval_status"] = str(row.get("ida_approval_status", "")).strip() if not pd.isna(row.get("ida_approval_status", None)) else "Pending"
            row_data["work_status"] = str(row.get("work_status", "")).strip() if not pd.isna(row.get("work_status", None)) else "Unsanctioned"
            row_data["house"] = str(row.get("house", "")).strip() if not pd.isna(row.get("house", None)) else None
            
            src_row = row.get("source_row_number", None)
            row_data["source_row_number"] = int(src_row) if (not pd.isna(src_row) and src_row is not None and str(src_row).isdigit()) else row_num

            dq_stat = row.get("data_quality_status", None)
            row_data["data_quality_status"] = str(dq_stat).strip() if not pd.isna(dq_stat) else "COMPLETE"
            
            d_src = row.get("data_source", None)
            row_data["data_source"] = str(d_src).strip() if not pd.isna(d_src) else "PUBLIC_MPLADS_DERIVED"

            # Check missing optional location
            if not row_data["constituency"] and not row_data["block"] and not row_data["village"]:
                has_warning = True
                missing_optional_count += 1
                row_issues.append({
                    "row_number": row_num,
                    "project_id": record_key,
                    "field": "location_text",
                    "issue_type": "WARNING_MISSING_OPTIONAL",
                    "message": "Detailed location fields (constituency/block/village) incomplete."
                })

            if is_rejected:
                row_status = "REJECTED"
                rejected_count += 1
            elif has_warning:
                row_status = "WARNING"
                warning_count += 1
            else:
                row_status = "VALID"
                valid_count += 1

            # Only return first 50 rows in clean_preview
            if len(clean_preview) < 50:
                clean_preview.append({
                    "row_number": row_num,
                    "status": row_status,
                    "data": row_data,
                    "issues": row_issues
                })

            # Cap total issues returned in JSON response to 500
            if len(all_issues) < 500 and row_issues:
                all_issues.extend(row_issues)

    return {
        "dataset_type": "PUBLIC_MPLADS_DERIVED",
        "filename": filename,
        "rows_received": rows_received,
        "valid_rows": valid_count,
        "warning_rows": warning_count,
        "rejected_rows": rejected_count,
        "duplicate_rows": duplicate_count,
        "missing_values": missing_optional_count,
        "clean_preview": clean_preview,
        "issues": all_issues
    }
