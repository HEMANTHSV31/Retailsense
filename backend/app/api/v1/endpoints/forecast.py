"""Forecast generation and history endpoints (org-scoped, MySQL-backed)."""

import uuid
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_org
from app.schemas.forecast import (
    ForecastGenerateRequest, ForecastHeaderResponse, ForecastDetailResponse,
    ForecastHistoryResponse, ForecastRecord,
)
from app.models.user import User
from app.models.organization import Organization
from app.models.forecast import ForecastHeader, Forecast
from app.services.forecasting import DemandForecaster
from app.services.data_service import TenantDataService

router = APIRouter()


@router.get("/options")
async def get_forecast_options(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Return available products and stores for the organization to forecast."""
    df = await TenantDataService.load_sales_df(db, org.id)
    if df.empty:
        return {
            "products": [],
            "stores": [],
            "models": [
                {"id": "random_forest", "label": "Random Forest Regressor"},
                {"id": "xgboost", "label": "XGBoost Regressor"},
                {"id": "lightgbm", "label": "LightGBM Regressor"},
                {"id": "baseline", "label": "Historical Mean Baseline"},
            ],
        }
    products = sorted([str(p) for p in df["item_id"].dropna().unique().tolist()])
    stores = sorted([str(s) for s in df["store_id"].dropna().unique().tolist()])
    return {
        "products": products,
        "stores": stores,
        "models": [
            {"id": "random_forest", "label": "Random Forest Regressor"},
            {"id": "xgboost", "label": "XGBoost Regressor"},
            {"id": "lightgbm", "label": "LightGBM Regressor"},
            {"id": "baseline", "label": "Historical Mean Baseline"},
        ],
    }


@router.post("/generate")
async def generate_forecast(
    request: ForecastGenerateRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Generate a demand forecast for a specific product/store combination (org-scoped)."""
    # Load the org's data from MySQL — not the shared CSV
    df = await TenantDataService.load_sales_df(db, org.id)
    if df.empty:
        raise HTTPException(status_code=404, detail="No data for this organization. Upload or ingest data first.")

    # Filter for the requested item + store
    item_store_data = df[(df["item_id"] == request.item_id) & (df["store_id"] == request.store_id)].sort_values("date")
    if len(item_store_data) == 0:
        raise HTTPException(status_code=404, detail=f"No data found for {request.item_id} at {request.store_id}")

    # Enrich with calendar and seasonal time features so ML captures cycles
    item_store_data = item_store_data.copy()
    item_store_data["date"] = pd.to_datetime(item_store_data["date"])
    item_store_data["year"] = item_store_data["date"].dt.year
    item_store_data["month"] = item_store_data["date"].dt.month
    item_store_data["day"] = item_store_data["date"].dt.day
    item_store_data["dayofweek"] = item_store_data["date"].dt.dayofweek
    item_store_data["quarter"] = item_store_data["date"].dt.quarter
    item_store_data["is_weekend"] = (item_store_data["dayofweek"] >= 5).astype(int)

    # Selected model type (defaulting to random_forest)
    chosen_model = request.model_type or "random_forest"
    if chosen_model not in ["random_forest", "xgboost", "lightgbm", "baseline"]:
        chosen_model = "random_forest"

    # Train or load the org's model
    model_path = f"models/{org.id}/best_model.joblib"
    forecaster = None
    if not request.model_type:
        try:
            forecaster = DemandForecaster()
            forecaster.load_model(model_path)
        except (FileNotFoundError, Exception):
            forecaster = None

    if forecaster is None:
        forecaster = DemandForecaster(model_type=chosen_model)
        forecaster.train_model(item_store_data)

    # Generate forecast
    forecast_df = forecaster.forecast_future(item_store_data, periods=request.horizon_days)

    if len(forecast_df) == 0:
        raise HTTPException(status_code=500, detail="Forecast generation returned no data")

    # Save forecast header (org-scoped)
    header = ForecastHeader(
        organization_id=org.id,
        model_type=forecaster.model_type,
        horizon_days=request.horizon_days,
        item_count=1,
        store_count=1,
        total_forecast=float(forecast_df["predicted_sales"].sum()),
        created_by=current_user.id,
    )
    db.add(header)
    await db.flush()

    # Build response
    records = []
    for _, row in forecast_df.iterrows():
        records.append({
            "id": str(uuid.uuid4()),
            "header_id": header.id,
            "item_id": request.item_id,
            "store_id": request.store_id,
            "forecast_date": row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])[:10],
            "predicted_sales": float(row["predicted_sales"]),
        })

    return {
        "header": ForecastHeaderResponse(
            id=header.id, dataset_id=None, model_type=header.model_type,
            horizon_days=header.horizon_days, item_count=1, store_count=1,
            total_forecast=header.total_forecast, created_by=current_user.id,
            created_at=header.created_at,
        ),
        "forecast": records,
        "summary": {
            "total_forecast": float(forecast_df["predicted_sales"].sum()),
            "avg_daily": float(forecast_df["predicted_sales"].mean()),
            "peak_day": forecast_df.loc[forecast_df["predicted_sales"].idxmax(), "date"].strftime("%Y-%m-%d") if len(forecast_df) > 0 else None,
            "peak_value": float(forecast_df["predicted_sales"].max()) if len(forecast_df) > 0 else 0,
        },
    }


@router.get("/history", response_model=ForecastHistoryResponse)
async def forecast_history(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Get forecast generation history for the active org."""
    result = await db.execute(
        select(ForecastHeader)
        .where(ForecastHeader.organization_id == org.id)
        .order_by(ForecastHeader.created_at.desc())
        .limit(50)
    )
    headers = result.scalars().all()
    return ForecastHistoryResponse(
        headers=[ForecastHeaderResponse.model_validate(h) for h in headers],
        total=len(headers),
    )


@router.get("/{forecast_id}", response_model=ForecastDetailResponse)
async def get_forecast(
    forecast_id: str,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Get full forecast details including all predictions (org-scoped)."""
    result = await db.execute(
        select(ForecastHeader).where(
            ForecastHeader.id == forecast_id,
            ForecastHeader.organization_id == org.id,
        )
    )
    header = result.scalar_one_or_none()
    if not header:
        raise HTTPException(status_code=404, detail="Forecast not found")

    return ForecastDetailResponse(
        id=header.id, dataset_id=header.dataset_id,
        model_type=header.model_type, horizon_days=header.horizon_days,
        item_count=header.item_count, store_count=header.store_count,
        total_forecast=header.total_forecast, created_by=header.created_by,
        created_at=header.created_at,
        details=[ForecastRecord.model_validate(d) for d in header.details],
    )


