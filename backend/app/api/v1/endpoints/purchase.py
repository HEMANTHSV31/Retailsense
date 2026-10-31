"""Purchase Decision Engine API — decisions, financials, what-if simulation."""

import pandas as pd

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_org
from app.schemas.purchase import (
    PurchaseDecisionsRequest, PurchaseDecisionsResponse, PurchaseDecisionItem,
    FinancialSummary, WhatIfRequest, WhatIfResponse,
)
from app.models.user import User
from app.models.organization import Organization
from app.services.data_service import TenantDataService
from app.services.purchase_engine import PurchaseDecisionEngine

router = APIRouter()


def _row_to_item(row) -> PurchaseDecisionItem:
    return PurchaseDecisionItem(
        item_id=row["item_id"], store_id=row["store_id"],
        avg_daily_demand=float(row["avg_daily_demand"]),
        demand_std=float(row["demand_std"]),
        safety_stock=float(row["safety_stock"]),
        reorder_point=float(row["reorder_point"]),
        eoq=float(row["eoq"]),
        recommended_order_qty=float(row["recommended_order_qty"]),
        order_today=bool(row["order_today"]),
        order_date=str(row["order_date"]),
        arrival_date=str(row["arrival_date"]),
        stockout_in_days=float(row["stockout_in_days"]) if pd.notna(row["stockout_in_days"]) else None,
        stockout_date=row["stockout_date"],
        status=str(row["status"]),
        days_of_stock=float(row["days_of_stock"]),
        unit_price=float(row["unit_price"]),
        inventory_value=float(row["inventory_value"]),
        excess_units=float(row["excess_units"]),
        overstock_capital=float(row["overstock_capital"]),
        stockout_revenue_loss=float(row["stockout_revenue_loss"]),
        carrying_cost=float(row["carrying_cost"]),
        inventory_turnover=float(row["inventory_turnover"]) if pd.notna(row["inventory_turnover"]) else None,
        days_of_inventory=float(row["days_of_inventory"]),
        potential_savings=float(row["potential_savings"]),
    )


def _financials_from(summary: dict) -> FinancialSummary:
    return FinancialSummary(**summary)


@router.post("/decisions", response_model=PurchaseDecisionsResponse)
async def purchase_decisions(
    request: PurchaseDecisionsRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Generate purchase decisions with financial intelligence for the org."""
    df = await TenantDataService.load_sales_df(db, org.id)
    if df.empty:
        return PurchaseDecisionsResponse(
            decisions=[],
            total_count=0,
            financials=None,
        )

    # Real stock levels when available
    inv_df = await TenantDataService.load_inventory_df(db, org.id)
    if not inv_df.empty:
        df = df.merge(inv_df, on=["item_id", "store_id"], how="left")
    if "current_stock" not in df.columns or df["current_stock"].isna().all():
        stock = df.groupby(["item_id", "store_id"])["sales"].transform(lambda x: max(x.tail(28).sum() * 1.5, 10))
        df = df.copy()
        df["current_stock"] = stock
    else:
        df["current_stock"] = df["current_stock"].fillna(0)

    demand_mult = request.demand_multiplier or PurchaseDecisionEngine.get_current_demand_multiplier()["multiplier"]

    engine = PurchaseDecisionEngine(
        service_level=request.service_level,
        lead_time_days=request.lead_time_days,
    )

    # Sample for speed
    combos = df[["item_id", "store_id"]].drop_duplicates()
    if len(combos) > request.sample_size:
        sampled = combos.sample(n=request.sample_size, random_state=42)
        df = df.merge(sampled, on=["item_id", "store_id"])

    decisions_df = engine.generate_purchase_decisions(df, demand_multiplier=demand_mult)

    financials = None
    if request.include_financials:
        financials = _financials_from(engine.financial_summary(decisions_df))

    items = [_row_to_item(row) for _, row in decisions_df.head(500).iterrows()]
    return PurchaseDecisionsResponse(
        decisions=items,
        total_count=len(decisions_df),
        financials=financials,
    )


@router.post("/financial-summary", response_model=FinancialSummary)
async def financial_summary(
    request: PurchaseDecisionsRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Get just the financial KPIs (inventory value, overstock capital, etc.)."""
    df = await TenantDataService.load_sales_df(db, org.id)
    if df.empty:
        return FinancialSummary(
            total_inventory_value=0.0,
            total_overstock_capital=0.0,
            total_stockout_loss_risk=0.0,
            total_carrying_cost=0.0,
            total_potential_savings=0.0,
            total_recommended_order_value=0.0,
            avg_inventory_turnover=0.0,
            avg_days_of_inventory=0.0,
            items_to_reorder=0,
        )

    inv_df = await TenantDataService.load_inventory_df(db, org.id)
    if not inv_df.empty:
        df = df.merge(inv_df, on=["item_id", "store_id"], how="left")
    if "current_stock" not in df.columns or df["current_stock"].isna().all():
        stock = df.groupby(["item_id", "store_id"])["sales"].transform(lambda x: max(x.tail(28).sum() * 1.5, 10))
        df = df.copy()
        df["current_stock"] = stock
    else:
        df["current_stock"] = df["current_stock"].fillna(0)

    demand_mult = request.demand_multiplier or PurchaseDecisionEngine.get_current_demand_multiplier()["multiplier"]
    engine = PurchaseDecisionEngine(service_level=request.service_level, lead_time_days=request.lead_time_days)

    decisions_df = engine.generate_purchase_decisions(df, demand_multiplier=demand_mult)
    return _financials_from(engine.financial_summary(decisions_df))


@router.post("/what-if", response_model=WhatIfResponse)
async def what_if_simulation(
    request: WhatIfRequest,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Run an inventory what-if scenario vs the current baseline."""
    import pandas as pd

    df = await TenantDataService.load_sales_df(db, org.id)
    if df.empty:
        zero_fin = FinancialSummary(
            total_inventory_value=0.0,
            total_overstock_capital=0.0,
            total_stockout_loss_risk=0.0,
            total_carrying_cost=0.0,
            total_potential_savings=0.0,
            total_recommended_order_value=0.0,
            avg_inventory_turnover=0.0,
            avg_days_of_inventory=0.0,
            items_to_reorder=0,
        )
        return WhatIfResponse(
            baseline_financials=zero_fin,
            scenario_financials=zero_fin,
            scenario={},
            deltas={},
            top_changes=[],
        )

    inv_df = await TenantDataService.load_inventory_df(db, org.id)
    if not inv_df.empty:
        df = df.merge(inv_df, on=["item_id", "store_id"], how="left")
    if "current_stock" not in df.columns or df["current_stock"].isna().all():
        stock = df.groupby(["item_id", "store_id"])["sales"].transform(lambda x: max(x.tail(28).sum() * 1.5, 10))
        df = df.copy()
        df["current_stock"] = stock
    else:
        df["current_stock"] = df["current_stock"].fillna(0)

    combos = df[["item_id", "store_id"]].drop_duplicates()
    if len(combos) > request.sample_size:
        sampled = combos.sample(n=request.sample_size, random_state=42)
        df = df.merge(sampled, on=["item_id", "store_id"])

    demand_mult = request.demand_multiplier or PurchaseDecisionEngine.get_current_demand_multiplier()["multiplier"]

    # Baseline
    baseline_engine = PurchaseDecisionEngine(service_level=0.95, lead_time_days=7)
    base_decisions = baseline_engine.generate_purchase_decisions(df, demand_multiplier=demand_mult)
    base_fin = baseline_engine.financial_summary(base_decisions)

    # Scenario
    scenario_engine = PurchaseDecisionEngine(
        service_level=request.service_level if request.service_level is not None else 0.95,
        lead_time_days=request.lead_time_days if request.lead_time_days is not None else 7,
        holding_cost_rate=request.holding_cost_rate if request.holding_cost_rate is not None else 0.25,
        order_cost=request.order_cost if request.order_cost is not None else 100.0,
        unit_cost=request.unit_cost if request.unit_cost is not None else 10.0,
        demand_growth=request.demand_growth if request.demand_growth is not None else 0.0,
    )
    scen_decisions = scenario_engine.generate_purchase_decisions(df, demand_multiplier=demand_mult)
    scen_fin = scenario_engine.financial_summary(scen_decisions)

    # Deltas (scenario − baseline)
    deltas = {}
    for key in base_fin:
        b = base_fin.get(key)
        s = scen_fin.get(key)
        if isinstance(b, (int, float)) and isinstance(s, (int, float)):
            deltas[key] = round(s - b, 2)
        else:
            deltas[key] = None

    # Top changes by |Δ recommended order qty|
    merged = base_decisions.merge(
        scen_decisions[["item_id", "store_id", "recommended_order_qty", "safety_stock", "days_of_stock"]],
        on=["item_id", "store_id"], suffixes=("_base", "_scen"),
    )
    merged["delta_qty"] = merged["recommended_order_qty_scen"] - merged["recommended_order_qty_base"]
    top = merged.reindex(merged["delta_qty"].abs().sort_values(ascending=False).index).head(10)
    top_changes = [{
        "item_id": r["item_id"], "store_id": r["store_id"],
        "order_qty_baseline": float(r["recommended_order_qty_base"]),
        "order_qty_scenario": float(r["recommended_order_qty_scen"]),
        "safety_stock_baseline": float(r["safety_stock_base"]),
        "safety_stock_scenario": float(r["safety_stock_scen"]),
        "days_of_stock_baseline": float(r["days_of_stock_base"]),
        "days_of_stock_scenario": float(r["days_of_stock_scen"]),
        "delta_qty": float(r["delta_qty"]),
    } for _, r in top.iterrows()]

    scenario_params = {
        "demand_growth": request.demand_growth,
        "lead_time_days": request.lead_time_days,
        "service_level": request.service_level,
        "holding_cost_rate": request.holding_cost_rate,
        "order_cost": request.order_cost,
        "unit_cost": request.unit_cost,
    }

    return WhatIfResponse(
        baseline_financials=_financials_from(base_fin),
        scenario_financials=_financials_from(scen_fin),
        scenario=scenario_params,
        deltas=deltas,
        top_changes=top_changes,
    )


