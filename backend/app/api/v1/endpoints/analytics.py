"""Analytics endpoints — dashboard overview, sales trends, product/store analysis.

v3: reads directly from the tenant-scoped MySQL tables (via
TenantDataService), so each organization's analytics reflect only its own
data.
"""

import pandas as pd

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_org
from app.schemas.analytics import (
    OverviewMetrics, SalesTrendPoint, TopProduct, StorePerformance,
    SeasonalBreakdown, DayOfWeekAnalysis,
)
from app.models.user import User
from app.models.organization import Organization
from app.services.data_service import TenantDataService

router = APIRouter()


async def _load_org_daily(db: AsyncSession, org_id: str) -> pd.DataFrame:
    """Load the org's sales as daily aggregates: date, store_id, total_sales, total_revenue, item_count."""
    df = await TenantDataService.load_sales_df(db, org_id)
    if df.empty:
        return pd.DataFrame(columns=["date", "store_id", "total_sales", "total_revenue", "item_count"])
    df["revenue"] = df["sales"] * df["sell_price"].fillna(0) if "sell_price" in df.columns else 0.0
    daily = df.groupby(["date", "store_id"]).agg(
        total_sales=("sales", "sum"),
        total_revenue=("revenue", "sum"),
        item_count=("item_id", "nunique"),
    ).reset_index()
    return daily


@router.get("/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard overview metrics for the active org."""
    df = await TenantDataService.load_sales_df(db, org.id)
    if df.empty:
        return OverviewMetrics(
            total_products=0,
            total_stores=0,
            total_categories=0,
            total_states=0,
            total_sales=0.0,
            avg_daily_sales=0.0,
            date_range=[],
            n_time_series=0,
            total_revenue=0.0,
        )

    total_sales = float(df["sales"].sum())
    revenue = float((df["sales"] * df["sell_price"].fillna(0)).sum()) if "sell_price" in df.columns else 0.0
    days = df["date"].nunique()
    avg_daily = total_sales / days if days else 0

    # State dimension: check state_id column or derive from store_id prefix (e.g. CA_1 -> CA)
    if "state_id" in df.columns and df["state_id"].notna().any():
        total_states = int(df["state_id"].nunique())
    elif "store_id" in df.columns and df["store_id"].notna().any():
        states = df["store_id"].astype(str).str.split("_").str[0]
        total_states = int(states.nunique())
    else:
        total_states = 1

    return OverviewMetrics(
        total_products=int(df["item_id"].nunique()),
        total_stores=int(df["store_id"].nunique()),
        total_categories=int(df["category"].nunique()) if "category" in df.columns and df["category"].notna().any() else 0,
        total_states=total_states,
        total_sales=total_sales,
        avg_daily_sales=avg_daily,
        date_range=[str(df["date"].min().date()), str(df["date"].max().date())],
        n_time_series=int(df.groupby(["item_id", "store_id"]).ngroups),
        total_revenue=revenue,
    )


@router.get("/sales-trend")
async def get_sales_trend(
    days: int = 90,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Get sales trend data for the last N days (daily totals across stores)."""
    daily = await _load_org_daily(db, org.id)
    if daily.empty:
        return []
    by_day = daily.groupby("date")["total_sales"].sum().reset_index().sort_values("date")
    if len(by_day) > days:
        by_day = by_day.tail(days)

    return [
        SalesTrendPoint(date=row["date"].date(), sales=float(row["total_sales"]))
        for _, row in by_day.iterrows()
    ]


@router.get("/top-products")
async def get_top_products(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Get the org's top-selling products."""
    df = await TenantDataService.load_sales_df(db, org.id)
    if df.empty:
        return []
    df["revenue"] = df["sales"] * df["sell_price"].fillna(0) if "sell_price" in df.columns else 0.0
    prods = df.groupby("item_id").agg(
        total_sales=("sales", "sum"),
        total_revenue=("revenue", "sum"),
        days_sold=("date", "nunique"),
        store_count=("store_id", "nunique"),
    ).sort_values("total_sales", ascending=False).head(limit)

    return [
        TopProduct(
            item_id=idx,
            total_sales=float(row["total_sales"]),
            avg_daily_sales=float(row["total_sales"] / row["days_sold"]) if row["days_sold"] else 0.0,
            store_count=int(row["store_count"]),
            total_revenue=round(float(row["total_revenue"]), 2),
        )
        for idx, row in prods.iterrows()
    ]


@router.get("/store-performance")
async def get_store_performance(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Get store performance comparison for the active org."""
    daily = await _load_org_daily(db, org.id)
    if daily.empty:
        return []
    stores = daily.groupby("store_id").agg(
        total_sales=("total_sales", "sum"),
        total_revenue=("total_revenue", "sum"),
        days=("date", "nunique"),
        item_count=("item_count", "max"),
    ).sort_values("total_sales", ascending=False)

    return [
        StorePerformance(
            store_id=idx,
            total_sales=float(row["total_sales"]),
            avg_daily_sales=float(row["total_sales"] / row["days"]) if row["days"] else 0.0,
            item_count=int(row["item_count"]),
            total_revenue=round(float(row["total_revenue"]), 2),
        )
        for idx, row in stores.iterrows()
    ]


@router.get("/seasonal")
async def get_seasonal_breakdown(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Get sales breakdown by season for the active org."""
    from app.services.weather_service import WeatherService

    daily = await _load_org_daily(db, org.id)
    if daily.empty:
        return []
    daily["season"] = daily["date"].apply(WeatherService.get_season)
    seasonal = daily.groupby("season").agg(
        total_sales=("total_sales", "sum"),
        days=("date", "nunique"),
    ).reset_index()

    return [
        SeasonalBreakdown(
            season=row["season"],
            avg_sales=float(row["total_sales"] / row["days"]) if row["days"] else 0.0,
            total_sales=float(row["total_sales"]),
            item_count=0,
        )
        for _, row in seasonal.iterrows()
    ]


@router.get("/day-of-week")
async def get_day_of_week_analysis(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Get sales analysis by day of week for the active org."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    daily = await _load_org_daily(db, org.id)
    if daily.empty:
        return []
    daily["dow"] = daily["date"].dt.dayofweek
    dow_avg = daily.groupby("dow")["total_sales"].mean()
    peak = dow_avg.max()

    return [
        DayOfWeekAnalysis(
            day=days[int(idx)],
            avg_sales=float(row),
            pct_of_peak=float((row / peak) * 100) if peak > 0 else 0,
        )
        for idx, row in dow_avg.items()
    ]


