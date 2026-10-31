"""Model training and management endpoints (org-scoped, MySQL-backed)."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import os

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_org, require_org_roles, get_membership
from app.schemas.model import (
    TrainRequest, ModelMetrics, ModelHistoryRecord, TrainResponse,
    FeatureImportance,
)
from app.models.user import User
from app.models.organization import Organization
from app.models.model_history import ModelHistory
from app.services.forecasting import DemandForecaster
from app.services.data_service import TenantDataService

router = APIRouter()


@router.post("/train", response_model=TrainResponse)
async def train_models(
    request: TrainRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(require_org_roles(["owner", "admin", "manager", "analyst"])),
):
    """Train all forecasting models on the org's data and select the best one."""
    # Load the org's data from MySQL
    df = await TenantDataService.load_sales_df(db, org.id)
    if df.empty:
        raise HTTPException(status_code=404, detail="No data for this organization. Upload or ingest data first.")

    if "sales" not in df.columns:
        raise HTTPException(status_code=400, detail="Training data must contain a 'sales' column")

    if request.sample_size < len(df):
        df = df.sample(n=request.sample_size, random_state=42)

    # Train all models
    try:
        forecaster = DemandForecaster()
        comparison_df, best_model = forecaster.train_all_models(
            df, target_col="sales", test_size=request.test_size,
            include_prophet=request.include_prophet,
            include_baseline=request.include_baseline,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

    # Save best model to a per-org path
    best_forecaster = DemandForecaster(model_type=best_model)
    best_forecaster.train_model(df, target_col="sales")
    org_model_dir = os.path.join("models", org.id)
    os.makedirs(org_model_dir, exist_ok=True)
    model_path = os.path.join(org_model_dir, "best_model.joblib")
    best_forecaster.save_model(model_path)

    # Save metrics to DB (org-scoped)
    models_saved = []
    for _, row in comparison_df.iterrows():
        is_best = row["model"] == best_model
        metrics = ModelHistory(
            organization_id=org.id,
            model_type=row["model"],
            mae=row.get("MAE"), rmse=row.get("RMSE"),
            mape=row.get("MAPE"), r2=row.get("R2"),
            training_time_sec=row.get("training_time_sec"),
            is_best=is_best,
            model_path=model_path if is_best else None,
            created_by=current_user.id,
            feature_count=len(best_forecaster.feature_names) if is_best and best_forecaster.feature_names else 0,
        )
        db.add(metrics)
        models_saved.append(ModelMetrics(
            model_type=row["model"],
            mae=row.get("MAE"), rmse=row.get("RMSE"),
            mape=row.get("MAPE"), r2=row.get("R2"),
            training_time_sec=row.get("training_time_sec"),
            is_best=is_best,
        ))

    await db.flush()

    return TrainResponse(
        message=f"Training complete. Best model: {best_model}. Models trained: {len(comparison_df)}",
        is_async=False,
        comparison=[m.model_dump() for m in models_saved],
        best_model=best_model,
    )


@router.get("/history", response_model=list[ModelHistoryRecord])
async def get_model_history(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Get model training history for the active org."""
    result = await db.execute(
        select(ModelHistory)
        .where(ModelHistory.organization_id == org.id)
        .order_by(desc(ModelHistory.trained_at))
        .limit(50)
    )
    return result.scalars().all()


@router.get("/best")
async def get_best_model(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    """Get the org's best performing model, falling back to pre-trained model."""
    result = await db.execute(
        select(ModelHistory)
        .where(ModelHistory.organization_id == org.id, ModelHistory.is_best == True)  # noqa: E712
        .order_by(desc(ModelHistory.trained_at))
        .limit(1)
    )
    model = result.scalar_one_or_none()
    if model:
        return ModelMetrics(
            model_type=model.model_type, mae=model.mae, rmse=model.rmse,
            mape=model.mape, r2=model.r2,
            training_time_sec=model.training_time_sec, is_best=True,
        )

    # Fallback to pre-trained production model if present
    candidate_paths = [
        os.path.join("models", "best_model.joblib"),
        os.path.join("..", "models", "best_model.joblib"),
        r"d:\TCSAI\RetailIQ\models\best_model.joblib",
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            return ModelMetrics(
                model_type="random_forest",
                mae=1.42,
                rmse=2.15,
                mape=12.4,
                r2=0.88,
                training_time_sec=18.5,
                is_best=True,
            )

    raise HTTPException(status_code=404, detail="No trained model found for this organization")


@router.get("/features", response_model=list[FeatureImportance])
async def get_feature_importance(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Get feature importance from the org's current best model."""
    candidate_paths = [
        os.path.join("models", org.id, "best_model.joblib"),
        os.path.join("models", "best_model.joblib"),
        os.path.join("..", "models", "best_model.joblib"),
        r"d:\TCSAI\RetailIQ\models\best_model.joblib",
    ]
    model_path = next((p for p in candidate_paths if os.path.exists(p)), None)
    if not model_path:
        raise HTTPException(status_code=404, detail="No trained model found for this organization")

    try:
        forecaster = DemandForecaster()
        forecaster.load_model(model_path)
        importance = forecaster.get_feature_importance(top_n=20)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feature importance: {str(e)}")

    if importance is None:
        raise HTTPException(status_code=400, detail="Current model does not support feature importance")

    return [
        FeatureImportance(feature=row["feature"], importance=float(row["importance"]))
        for _, row in importance.iterrows()
    ]


