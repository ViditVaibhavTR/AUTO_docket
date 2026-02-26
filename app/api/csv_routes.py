"""
CSV upload endpoint — parse a CSV file and run multi-docket automation.
"""

import csv
import io

from fastapi import HTTPException, UploadFile, File, Form, status

from api.app import app
from api.docket_routes import multi_process_dockets
from models.schemas import MultiDocketConfig, MultiDocketRequest, MultiDocketResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Expected CSV columns
REQUIRED_COLUMNS = {"State", "District", "Case Number", "Name", "Email", "Frequency", "Alert Times"}
OPTIONAL_COLUMNS = {"Description"}
VALID_FREQUENCIES = {"daily", "weekdays", "weekly", "biweekly", "monthly"}
VALID_ALERT_TIMES = {"5am", "12pm", "3pm", "5pm"}


@app.post("/api/v1/docket/upload-csv", response_model=MultiDocketResponse)
async def upload_csv(
    file: UploadFile = File(..., description="CSV file with docket configurations"),
    session_id: str = Form(..., description="Active browser session ID"),
):
    """
    Upload a CSV file to run multi-docket automation.

    CSV columns: State, District, Case Number, Name, Description (optional),
    Email, Frequency, Alert Times (pipe-separated e.g. 5am|12pm|3pm|5pm)
    """
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a .csv file",
        )

    # Read and decode CSV
    try:
        raw = await file.read()
        text = raw.decode("utf-8-sig")  # utf-8-sig handles BOM from Excel
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read CSV file: {e}",
        )

    reader = csv.DictReader(io.StringIO(text))

    # Validate headers
    if reader.fieldnames is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty or has no header row",
        )

    headers = {h.strip() for h in reader.fieldnames}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV is missing required columns: {', '.join(sorted(missing))}",
        )

    # Parse rows
    dockets: list[MultiDocketConfig] = []
    errors: list[str] = []

    for row_num, row in enumerate(reader, start=2):  # row 1 is header
        # Strip whitespace from all values
        row = {k.strip(): (v.strip() if v else "") for k, v in row.items()}

        # Validate required fields
        state = row.get("State", "")
        district = row.get("District", "")
        case_number = row.get("Case Number", "")
        name = row.get("Name", "")
        email = row.get("Email", "")
        frequency = row.get("Frequency", "daily").lower()
        alert_times_raw = row.get("Alert Times", "5am|12pm|3pm|5pm")
        description = row.get("Description", "")

        if not state:
            errors.append(f"Row {row_num}: State is empty")
            continue
        if not district:
            errors.append(f"Row {row_num}: District is empty")
            continue
        if not case_number:
            errors.append(f"Row {row_num}: Case Number is empty")
            continue
        if not name:
            errors.append(f"Row {row_num}: Name is empty")
            continue
        if not email:
            errors.append(f"Row {row_num}: Email is empty")
            continue

        if frequency not in VALID_FREQUENCIES:
            errors.append(f"Row {row_num}: Invalid frequency '{frequency}'. Must be one of: {', '.join(sorted(VALID_FREQUENCIES))}")
            continue

        # Parse alert times (pipe-separated)
        alert_times = [t.strip().lower() for t in alert_times_raw.split("|") if t.strip()]
        invalid_times = [t for t in alert_times if t not in VALID_ALERT_TIMES]
        if invalid_times:
            errors.append(f"Row {row_num}: Invalid alert times: {', '.join(invalid_times)}. Must be from: {', '.join(sorted(VALID_ALERT_TIMES))}")
            continue
        if not alert_times:
            alert_times = ["5am", "12pm", "3pm", "5pm"]

        dockets.append(MultiDocketConfig(
            state=state,
            district=district,
            docket_number=case_number,
            alert_name=name,
            alert_description=description,
            user_email=email,
            frequency=frequency,
            alert_times=alert_times,
        ))

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV validation errors:\n" + "\n".join(errors),
        )

    if not dockets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV has no data rows",
        )

    if len(dockets) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV has {len(dockets)} rows, maximum is 20",
        )

    logger.info(f"CSV parsed successfully: {len(dockets)} dockets")
    for i, d in enumerate(dockets, 1):
        logger.info(f"  [{i}] {d.state} / {d.district} / {d.docket_number} / {d.alert_name}")

    # Build request and delegate to existing multi-process endpoint
    request = MultiDocketRequest(session_id=session_id, dockets=dockets)
    return await multi_process_dockets(request)
