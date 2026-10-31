"""Inventory optimization endpoints (org-scoped, MySQL-backed)."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_org
from app.schemas.inventory import (
    InventoryRequest, InventoryRecommendationItem, StockoutPrediction, OverstockItem,
)
from app.models.user import User
from app.models.organization import Organization
from app.services.inventory_optimizer import InventoryOptimizer
from app.services.data_service import TenantDataService

router = APIRouter()


@router.post("/recommendations")
async def generate_recommendations(
    request: InventoryRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Generate inventory optimization recommendations for the active org."""
    # Load the org's sales data from MySQL
    df = await TenantDataService.load_sales_df(db, org.id)
    if df.empty:
        return {
            "recommendations": [],
            "total_count": 0,
            "metrics": {
                "total_items": 0,
                "items_ok": 0,
                "items_low": 0,
                "items_critical": 0,
                "items_excess": 0,
                "avg_days_of_stock": 0.0,
                "total_safety_stock": 0.0,
                "total_recommended_orders": 0.0,
                "items_need_reorder": 0,
            },
            "stockout_predictions": [],
            "overstock_items": [],
        }

    # Real stock levels when available; otherwise estimate with realistic distribution
    inv_df = await TenantDataService.load_inventory_df(db, org.id)
    if not inv_df.empty:
        df = df.merge(inv_df, on=["item_id", "store_id"], how="left")
    if "current_stock" not in df.columns or df["current_stock"].isna().all():
        def assign_stock(group):
            mean_demand = group["sales"].tail(28).mean()
            h = abs(hash(f"{group.name[0]}_{group.name[1]}")) % 4
            if h == 0:
                qty = max(mean_demand * 4.0, 5)
            elif h == 1:
                qty = max(mean_demand * 10.0, 15)
            elif h == 2:
                qty = max(mean_demand * 70.0, 100)
            else:
                qty = max(mean_demand * 28.0, 50)
            return qty

        stock_map = df.groupby(["item_id", "store_id"]).apply(assign_stock).to_dict()
        df = df.copy()
        df["current_stock"] = df.apply(lambda r: stock_map.get((r["item_id"], r["store_id"]), 50.0), axis=1)
    else:
        df["current_stock"] = df["current_stock"].fillna(0)

    # Get demand multiplier
    demand_mult = request.demand_multiplier or InventoryOptimizer.get_current_demand_multiplier()["multiplier"]

    # Sample if needed
    combos = df[["item_id", "store_id"]].drop_duplicates()
    if len(combos) > request.sample_size:
        sampled = combos.sample(n=request.sample_size, random_state=42)
        df = df.merge(sampled, on=["item_id", "store_id"])

    # Run optimizer
    optimizer = InventoryOptimizer(service_level=request.service_level)
    recommendations = optimizer.generate_inventory_recommendations(
        df, demand_multiplier=demand_mult, lead_time_days=request.lead_time_days
    )

    if len(recommendations) == 0:
        raise HTTPException(status_code=500, detail="No recommendations generated")

    # Calculate metrics
    metrics = optimizer.calculate_inventory_metrics(recommendations)
    items_need_reorder = int((recommendations["recommended_order_qty"] > 0).sum())

    # Stockout predictions
    stockout_predictions = []
    for _, row in recommendations.iterrows():
        stockout = optimizer.predict_stockout_date(row["current_stock"], row["avg_daily_demand"])
        if stockout and stockout["days_remaining"] < 90:
            stockout_predictions.append({
                "item_id": row["item_id"], "store_id": row["store_id"],
                "current_stock": float(row["current_stock"]),
                "avg_daily_demand": float(row["avg_daily_demand"]),
                "days_remaining": stockout["days_remaining"],
                "predicted_stockout_date": stockout["predicted_date"],
                "is_critical": stockout["is_critical"],
            })

    # Overstock
    overstock_items = []
    for _, row in recommendations.iterrows():
        overstock = optimizer.detect_overstock(row["current_stock"], row["avg_daily_demand"], request.excess_threshold_days)
        if overstock["is_overstock"]:
            overstock_items.append({
                "item_id": row["item_id"], "store_id": row["store_id"],
                "current_stock": float(row["current_stock"]),
                "avg_daily_demand": float(row["avg_daily_demand"]),
                "days_of_stock": overstock["days_of_stock"],
                "excess_units": overstock["excess_units"],
                "reason": overstock["reason"],
            })

    # Build response items
    items = []
    for _, row in recommendations.head(100).iterrows():
        items.append(InventoryRecommendationItem(
            item_id=row["item_id"], store_id=row["store_id"],
            current_stock=float(row["current_stock"]),
            avg_daily_demand=float(row["avg_daily_demand"]),
            demand_std=float(row["demand_std"]),
            safety_stock=float(row["safety_stock"]),
            reorder_point=float(row["reorder_point"]),
            eoq=float(row["eoq"]),
            recommended_order_qty=float(row["recommended_order_qty"]),
            status=row["status"], days_of_stock=float(row["days_of_stock"]),
            stockout_in_days=float(row.get("stockout_in_days", 999)),
            stockout_date=str(row.get("stockout_date", "N/A")),
            demand_multiplier_used=float(row["demand_multiplier_used"]),
        ))

    return {
        "recommendations": items,
        "total_count": len(recommendations),
        "metrics": {
            "total_items": metrics["total_items"],
            "items_ok": metrics["items_ok"],
            "items_low": metrics["items_low"],
            "items_critical": metrics["items_critical"],
            "items_excess": metrics["items_excess"],
            "avg_days_of_stock": round(metrics["avg_days_of_stock"], 1),
            "total_safety_stock": round(metrics["total_safety_stock"], 0),
            "total_recommended_orders": round(metrics["total_recommended_orders"], 0),
            "items_need_reorder": items_need_reorder,
        },
        "stockout_predictions": stockout_predictions[:50],
        "overstock_items": overstock_items[:50],
    }


@router.get("/demand-multiplier")
async def get_demand_multiplier():
    """Get the current demand multiplier based on season, weather, and holidays."""
    return InventoryOptimizer.get_current_demand_multiplier()


@router.get("/seasonal-advice")
async def get_seasonal_advice():
    """Get seasonal product advice and holiday stock recommendations."""
    return {"advice": InventoryOptimizer.get_holiday_stock_advice()}


