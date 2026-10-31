"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, users, organizations, data, forecast, inventory, analytics, upload,
    model, model_registry, purchase, alerts, intelligence, advisor, data_health,
    reports, ops, weather, insights, decisions
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(decisions.router, prefix="/decisions", tags=["Decision Intelligence"])
api_router.include_router(data.router, prefix="/data", tags=["Data Ingestion"])
api_router.include_router(model_registry.router, prefix="/model-registry", tags=["Model Registry"])
api_router.include_router(purchase.router, prefix="/purchase", tags=["Purchase Engine"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Smart Alerts"])
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["Executive & Intelligence"])
api_router.include_router(advisor.router, prefix="/advisor", tags=["AI Business Advisor"])
api_router.include_router(data_health.router, prefix="/data-health", tags=["Data Health"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reporting"])
api_router.include_router(ops.router, prefix="/ops", tags=["Operations"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(forecast.router, prefix="/forecast", tags=["Forecast"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(model.router, prefix="/model", tags=["Model Training"])
api_router.include_router(insights.router, prefix="/insights", tags=["Insights"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])


