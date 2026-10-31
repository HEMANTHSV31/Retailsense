"""CSV upload endpoints — upload, validate, preview, history."""

import os
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pandas as pd

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.schemas.upload import UploadResponse, DatasetInfo
from app.models.user import User
from app.models.dataset import Dataset, DatasetStatus
from app.services.upload_service import DataValidator

logger = logging.getLogger(__name__)

router = APIRouter()


ALLOWED_EXTENSIONS = (".csv", ".xlsx", ".xls", ".tsv", ".txt")


@router.post("/reset")
async def reset_organization_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Purge all sales, inventory levels, forecasts, products, stores and uploaded datasets for this organization."""
    from sqlalchemy import text
    org_id = current_user.organization_id
    if not org_id:
        from app.models.organization import Organization
        res_org = await db.execute(select(Organization))
        first_org = res_org.scalars().first()
        org_id = first_org.id if first_org else None

    if org_id:
        await db.execute(text("DELETE FROM sales WHERE organization_id = :org_id"), {"org_id": org_id})
        await db.execute(text("DELETE FROM inventory_levels WHERE organization_id = :org_id"), {"org_id": org_id})
        await db.execute(text("DELETE FROM forecasts WHERE header_id IN (SELECT id FROM forecast_headers WHERE organization_id = :org_id)"), {"org_id": org_id})
        await db.execute(text("DELETE FROM forecast_headers WHERE organization_id = :org_id"), {"org_id": org_id})
        await db.execute(text("DELETE FROM datasets WHERE organization_id = :org_id"), {"org_id": org_id})
        await db.execute(text("DELETE FROM import_jobs WHERE organization_id = :org_id"), {"org_id": org_id})
        await db.execute(text("DELETE FROM products WHERE organization_id = :org_id"), {"org_id": org_id})
        await db.execute(text("DELETE FROM stores WHERE organization_id = :org_id"), {"org_id": org_id})
    else:
        for t in ["sales", "inventory_levels", "forecasts", "forecast_headers", "datasets", "import_jobs", "products", "stores"]:
            await db.execute(text(f"DELETE FROM {t}"))

    await db.commit()
    return {"status": "success", "message": "All dummy data cleared. Ready for new data insertion."}


@router.post("/", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a CSV or Excel (.xlsx, .xls) file. Validates, stores, and returns processing status."""
    if not file.filename or not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported formats: Excel (.xlsx, .xls) or CSV (.csv, .tsv)",
        )

    # Save file to disk
    upload_dir = os.path.join(settings.DATA_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{file.filename}"
    filepath = os.path.join(upload_dir, safe_filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Validate file (supports CSV and Excel alike)
    validation = DataValidator.validate_file(filepath)

    # Resolve organization id
    org_id = current_user.organization_id
    if not org_id:
        from app.models.organization import Organization
        res_org = await db.execute(select(Organization))
        first_org = res_org.scalars().first()
        org_id = first_org.id if first_org else str(uuid.uuid4())

    # Create dataset record
    dataset = Dataset(
        organization_id=org_id,
        filename=safe_filename,
        original_filename=file.filename,
        row_count=validation["row_count"],
        column_count=validation["column_count"],
        file_size_kb=round(len(content) / 1024, 2),
        status=DatasetStatus.VALIDATING if validation["valid"] else DatasetStatus.ERROR,
        error_message="; ".join(validation["errors"]) if validation["errors"] else None,
        uploaded_by=current_user.id,
    )

    db.add(dataset)
    await db.flush()

    # Automatically ingest valid data into the organization's database tables
    if validation["valid"]:
        try:
            df = DataValidator.load_dataframe(filepath)
            if org_id:
                from app.services.data_service import TenantDataService
                await TenantDataService.ingest_dataframe(db, org_id, df, source=file.filename, created_by=current_user.id)
                dataset.status = DatasetStatus.CLEANED
                await db.commit()
        except Exception as e:
            logger.warning(f"Auto-ingestion during upload failed: {e}")

    await db.refresh(dataset)

    return UploadResponse(
        id=dataset.id,
        filename=file.filename,
        row_count=validation["row_count"],
        column_count=validation["column_count"],
        file_size_kb=dataset.file_size_kb,
        status=dataset.status.value,
        warnings=validation.get("warnings", []),
        errors=validation.get("errors", []),
    )


@router.get("/history", response_model=list[DatasetInfo])
async def upload_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get upload history for the current user."""
    result = await db.execute(
        select(Dataset).where(Dataset.uploaded_by == current_user.id).order_by(Dataset.created_at.desc()).limit(50)
    )
    return result.scalars().all()


@router.post("/{dataset_id}/clean")
async def clean_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Auto-clean a previously uploaded dataset."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    filepath = os.path.join(settings.DATA_DIR, "uploads", dataset.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found on disk")

    df = DataValidator.load_dataframe(filepath)
    validation_result = DataValidator.validate_file(filepath)
    df_clean = DataValidator.auto_clean(df, validation_result)

    # Save cleaned version
    clean_path = os.path.join(settings.DATA_DIR, "processed", f"cleaned_{dataset.filename}")
    os.makedirs(os.path.dirname(clean_path), exist_ok=True)
    df_clean.to_csv(clean_path, index=False)

    dataset.status = DatasetStatus.CLEANED
    dataset.row_count = len(df_clean)

    # Ingest cleaned data into organization's tables
    org_id = current_user.organization_id
    if org_id:
        from app.services.data_service import TenantDataService
        await TenantDataService.ingest_dataframe(db, org_id, df_clean, source=dataset.filename, created_by=current_user.id)
        await db.commit()

    await db.flush()

    return {"status": "cleaned", "row_count": len(df_clean), "path": clean_path}


