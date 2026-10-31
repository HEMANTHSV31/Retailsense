"""Pydantic schemas for analytics endpoints."""

from datetime import datetime, date
from pydantic import BaseModel, Field


class OverviewMetrics(BaseModel):
    total_products: int
    total_stores: int
    total_categories: int
    total_states: int
    total_sales: float
    avg_daily_sales: float
    date_range: list[str]
    n_time_series: int
    total_revenue: float = 0.0


class SalesTrendPoint(BaseModel):
    date: date
    sales: float
    is_forecast: bool = False


class TopProduct(BaseModel):
    item_id: str
    total_sales: float
    avg_daily_sales: float
    store_count: int
    total_revenue: float = 0.0


class StorePerformance(BaseModel):
    store_id: str
    total_sales: float
    avg_daily_sales: float
    item_count: int
    total_revenue: float = 0.0


class SeasonalBreakdown(BaseModel):
    season: str
    avg_sales: float
    total_sales: float
    item_count: int


class DayOfWeekAnalysis(BaseModel):
    day: str
    avg_sales: float
    pct_of_peak: float


class AnalyticsResponse(BaseModel):
    overview: OverviewMetrics | None = None
    sales_trend: list[SalesTrendPoint] = []
    top_products: list[TopProduct] = []
    store_performance: list[StorePerformance] = []
    seasonal_breakdown: list[SeasonalBreakdown] = []
    day_of_week: list[DayOfWeekAnalysis] = []


