# Column alias dictionary for normalising raw CSV/XLSX header variations to standard schema keys

COLUMN_ALIASES = {
    # project_id
    "project_id": "project_id",
    "project id": "project_id",
    "projectid": "project_id",
    "work_id": "project_id",
    "work id": "project_id",
    "sl_no": "project_id",

    # project_name
    "project_name": "project_name",
    "project name": "project_name",
    "name": "project_name",
    "work_name": "project_name",
    "work name": "project_name",
    "description": "project_name",
    "project_description": "project_name",

    # district
    "district": "district",
    "district_name": "district",
    "district name": "district",

    # project_type
    "project_type": "project_type",
    "project type": "project_type",
    "type": "project_type",
    "sector": "project_type",
    "category": "project_type",

    # sanctioned_amount
    "sanctioned_amount": "sanctioned_amount",
    "sanctioned amount": "sanctioned_amount",
    "sanction_amount": "sanctioned_amount",
    "sanctioned_cost": "sanctioned_amount",
    "sanctioned cost": "sanctioned_amount",
    "budget": "sanctioned_amount",
    "cost": "sanctioned_amount",

    # expenditure
    "expenditure": "expenditure",
    "actual_expenditure": "expenditure",
    "actual expenditure": "expenditure",
    "expense": "expenditure",
    "amount_spent": "expenditure",
    "spent": "expenditure",

    # sanction_date
    "sanction_date": "sanction_date",
    "sanction date": "sanction_date",
    "sanctioned_date": "sanction_date",
    "start_date": "sanction_date",
    "sanction_dt": "sanction_date",

    # expected_completion_date
    "expected_completion_date": "expected_completion_date",
    "expected completion date": "expected_completion_date",
    "target_date": "expected_completion_date",
    "target completion date": "expected_completion_date",
    "due_date": "expected_completion_date",

    # actual_completion_date
    "actual_completion_date": "actual_completion_date",
    "actual completion date": "actual_completion_date",
    "completion_date": "actual_completion_date",
    "actual_date": "actual_completion_date",

    # progress_percent
    "progress_percent": "progress_percent",
    "progress percent": "progress_percent",
    "progress": "progress_percent",
    "progress %": "progress_percent",
    "progress_percentage": "progress_percent",
    "physical_progress": "progress_percent",
    "percent": "progress_percent",

    # latitude
    "latitude": "latitude",
    "lat": "latitude",

    # longitude
    "longitude": "longitude",
    "long": "longitude",
    "lng": "longitude",

    # status
    "status": "status",
    "project_status": "status",
    "work_status": "status",

    # supporting_document
    "supporting_document": "supporting_document",
    "supporting document": "supporting_document",
    "document": "supporting_document",
    "file": "supporting_document",
    "doc": "supporting_document",
}

def normalise_column_name(raw_col: str) -> str:
    """Normalises a raw column header string using lowercase stripping and alias matching."""
    if not isinstance(raw_col, str):
        return str(raw_col)
    
    clean_col = raw_col.strip().lower()
    return COLUMN_ALIASES.get(clean_col, clean_col)
