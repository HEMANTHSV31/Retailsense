"""Inventory optimization service with Pakistan holiday/season demand multipliers."""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class InventoryOptimizer:
    """Inventory optimization with safety stock, reorder point, EOQ, and stockout prediction."""

    def __init__(self, service_level=0.95):
        self.service_level = service_level
        self.z_score = self._get_z_score(service_level)

    def _get_z_score(self, service_level):
        from scipy import stats
        return stats.norm.ppf(service_level)

    def calculate_safety_stock(self, demand_std, lead_time_days=7):
        safety_stock = self.z_score * demand_std * np.sqrt(lead_time_days)
        return np.maximum(safety_stock, 0)

    def calculate_reorder_point(self, avg_demand, demand_std, lead_time_days=7):
        lead_time_demand = avg_demand * lead_time_days
        safety_stock = self.calculate_safety_stock(demand_std, lead_time_days)
        return lead_time_demand + safety_stock

    def calculate_economic_order_quantity(self, annual_demand, order_cost=100, holding_cost_rate=0.25, unit_cost=10):
        if annual_demand <= 0:
            return 0
        holding_cost = unit_cost * holding_cost_rate
        eoq = np.sqrt((2 * annual_demand * order_cost) / holding_cost)
        return np.maximum(eoq, 1)

    def optimize_inventory_for_item(self, historical_sales, lead_time_days=7, demand_multiplier=1.0):
        """Optimize inventory for a single item."""
        if len(historical_sales) == 0:
            return {"avg_demand": 0, "demand_std": 0, "safety_stock": 0, "reorder_point": 0, "eoq": 0}

        avg_demand = historical_sales.mean() * demand_multiplier
        demand_std = historical_sales.std()
        if pd.isna(demand_std) or demand_std == 0:
            demand_std = avg_demand * 0.1

        safety_stock = self.calculate_safety_stock(demand_std, lead_time_days)
        reorder_point = self.calculate_reorder_point(avg_demand, demand_std, lead_time_days)
        annual_demand = avg_demand * 365
        eoq = self.calculate_economic_order_quantity(annual_demand)

        return {
            "avg_demand": avg_demand, "demand_std": demand_std,
            "safety_stock": safety_stock, "reorder_point": reorder_point,
            "eoq": eoq, "demand_multiplier_applied": demand_multiplier,
        }

    def generate_inventory_recommendations(self, df, current_stock_col="current_stock", demand_multiplier=1.0, lead_time_days=7):
        """Generate inventory recommendations for all items."""
        recommendations = []
        item_store_groups = df.groupby(["item_id", "store_id"])

        for (item_id, store_id), group in item_store_groups:
            if "sales" not in group.columns:
                continue
            historical_sales = group["sales"].values
            optimization = self.optimize_inventory_for_item(historical_sales, lead_time_days=lead_time_days, demand_multiplier=demand_multiplier)
            current_stock = group[current_stock_col].iloc[-1] if current_stock_col in group.columns else 0

            status = "OK"
            if current_stock < optimization["safety_stock"]:
                status = "CRITICAL"
            elif current_stock < optimization["reorder_point"]:
                status = "LOW"
            elif current_stock > optimization["reorder_point"] + optimization["eoq"]:
                status = "EXCESS"

            recommendation = {
                "item_id": item_id, "store_id": store_id,
                "current_stock": current_stock,
                "avg_daily_demand": optimization["avg_demand"],
                "demand_std": optimization["demand_std"],
                "safety_stock": optimization["safety_stock"],
                "reorder_point": optimization["reorder_point"],
                "eoq": optimization["eoq"],
                "recommended_order_qty": max(0, optimization["reorder_point"] - current_stock),
                "status": status,
                "days_of_stock": current_stock / optimization["avg_demand"] if optimization["avg_demand"] > 0 else 999,
                "demand_multiplier_used": demand_multiplier,
            }

            stockout = self.predict_stockout_date(current_stock, optimization["avg_demand"])
            recommendation["stockout_in_days"] = stockout["days_remaining"] if stockout else 999
            recommendation["stockout_date"] = stockout["predicted_date"] if stockout else "N/A"

            overstock = self.detect_overstock(current_stock, optimization["avg_demand"])
            recommendation["is_overstock"] = overstock["is_overstock"]
            if overstock["is_overstock"]:
                recommendation["excess_units"] = overstock["excess_units"]

            recommendations.append(recommendation)

        return pd.DataFrame(recommendations)

    def identify_stockout_risk(self, recommendations_df, threshold_days=7):
        """Identify items at risk of stockout."""
        at_risk = recommendations_df[
            (recommendations_df["days_of_stock"] < threshold_days) |
            (recommendations_df["status"].isin(["LOW", "CRITICAL"]))
        ].copy()
        return at_risk.sort_values("days_of_stock")

    def identify_excess_inventory(self, recommendations_df, excess_threshold=2):
        """Identify items with excess inventory."""
        excess = recommendations_df[
            recommendations_df["days_of_stock"] > (excess_threshold * 30)
        ].copy()
        return excess.sort_values("days_of_stock", ascending=False)

    def predict_stockout_date(self, current_stock, avg_daily_demand):
        """Predict when stock will run out."""
        if avg_daily_demand <= 0:
            return None
        days_until_stockout = current_stock / avg_daily_demand
        if days_until_stockout >= 365:
            return None
        predicted_date = datetime.now() + timedelta(days=int(days_until_stockout))
        return {
            "days_remaining": round(days_until_stockout, 1),
            "predicted_date": predicted_date.strftime("%Y-%m-%d"),
            "is_critical": days_until_stockout < 7,
        }

    def detect_overstock(self, current_stock, avg_daily_demand, excess_threshold_days=60):
        """Detect overstock situations."""
        if avg_daily_demand <= 0:
            return {"is_overstock": False, "days_of_stock": float("inf"), "reason": "No demand"}
        days_of_stock = current_stock / avg_daily_demand
        return {
            "is_overstock": days_of_stock > excess_threshold_days,
            "days_of_stock": round(days_of_stock, 1),
            "excess_units": max(0, current_stock - (avg_daily_demand * excess_threshold_days)),
            "reason": f"Stock covers {days_of_stock:.0f} days (threshold: {excess_threshold_days})",
        }

    def calculate_inventory_metrics(self, recommendations_df):
        """Calculate overall inventory KPIs."""
        return {
            "total_items": len(recommendations_df),
            "items_ok": len(recommendations_df[recommendations_df["status"] == "OK"]),
            "items_low": len(recommendations_df[recommendations_df["status"] == "LOW"]),
            "items_critical": len(recommendations_df[recommendations_df["status"] == "CRITICAL"]),
            "items_excess": len(recommendations_df[recommendations_df["status"] == "EXCESS"]),
            "avg_days_of_stock": recommendations_df["days_of_stock"].mean(),
            "total_safety_stock": recommendations_df["safety_stock"].sum(),
            "total_recommended_orders": recommendations_df["recommended_order_qty"].sum(),
        }

    # ── Pakistan season/holiday demand multipliers ──────────────────────────

    @staticmethod
    def get_current_demand_multiplier(weather_service=None, holiday_service=None) -> dict:
        """Get demand multiplier based on current Pakistan season + upcoming holidays."""
        from app.services.weather_service import WeatherService
        from app.services.holiday_service import HolidayService

        ws = weather_service or WeatherService()
        hs = holiday_service or HolidayService()

        now = datetime.now()
        season = WeatherService.get_season(now)
        multiplier = 1.0
        reasons = []

        season_multipliers = {
            "Summer": 1.15, "Monsoon": 1.05, "Winter": 1.10,
            "Spring": 1.0, "Autumn": 1.0,
        }
        season_mult = season_multipliers.get(season, 1.0)
        if season_mult > 1.0:
            multiplier *= season_mult
            reasons.append(f"{season} season ({season_mult}x)")

        pre_window = hs.is_in_pre_holiday_window(now)
        if pre_window:
            holiday_mult = pre_window.get("demand_multiplier", 1.0)
            multiplier *= holiday_mult
            reasons.append(f"Pre-{pre_window.get('holiday_name', 'holiday')} window ({holiday_mult}x)")

        weather_data = ws.fetch_current_weather()
        temp = weather_data.get("temperature_c", 25)
        if temp >= 35:
            multiplier *= 1.2
            reasons.append(f"Extreme heat ({temp:.0f}°C - 1.2x)")
        elif temp <= 10:
            multiplier *= 1.15
            reasons.append(f"Cold wave ({temp:.0f}°C - 1.15x)")

        return {
            "multiplier": round(multiplier, 2), "reasons": reasons,
            "season": season, "has_pre_holiday": bool(pre_window),
            "pre_holiday_info": pre_window,
        }

    @staticmethod
    def get_holiday_stock_advice(holiday_service=None) -> list:
        """Get actionable inventory advice for upcoming Pakistan holidays/seasons."""
        from app.services.holiday_service import HolidayService
        hs = holiday_service or HolidayService()
        now = datetime.now()
        upcoming = hs.get_upcoming_holidays(now, limit=10)
        advice_list = []

        for _, holiday in upcoming.iterrows():
            h_name = holiday["name"]
            h_date = holiday["date"]
            days_until = holiday.get("days_until", (h_date - pd.Timestamp(now)).days)
            advice_text = holiday.get("advice", "")
            if advice_text:
                advice_list.append({
                    "type": "holiday_stock_up", "holiday": h_name,
                    "date": h_date.strftime("%Y-%m-%d") if hasattr(h_date, "strftime") else str(h_date)[:10],
                    "days_until": int(days_until),
                    "priority": "high" if days_until <= 14 else "medium" if days_until <= 30 else "low",
                    "suggestion": advice_text,
                    "demand_multiplier": hs.get_demand_multiplier(h_name),
                })
        return advice_list

    @staticmethod
    def check_seasonal_product_alerts(product_name: str, weather_service=None) -> dict:
        """Check if a product has seasonal demand alerts based on its name/keywords."""
        from app.services.weather_service import WeatherService, SEASONAL_PRODUCT_DEMAND
        now = datetime.now()
        season = WeatherService.get_season(now)
        season_info = SEASONAL_PRODUCT_DEMAND.get(season, {})
        product_lower = product_name.lower()

        for keyword in season_info.get("high_demand_keywords", []):
            if keyword.lower() in product_lower:
                return {
                    "alert": "high_demand", "season": season,
                    "message": f"⚠️ **{product_name}** is in high demand during {season}. Increase stock.",
                    "action": "Increase stock",
                }
        for keyword in season_info.get("low_demand_keywords", []):
            if keyword.lower() in product_lower:
                return {
                    "alert": "low_demand", "season": season,
                    "message": f"ℹ️ **{product_name}** has lower demand during {season}. Reduce stock.",
                    "action": "Reduce stock",
                }
        return {"alert": "normal", "season": season, "message": "", "action": ""}


