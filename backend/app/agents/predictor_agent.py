"""Predictor Agent — Step 2 of the Autonomous Decision Intelligence Loop.

Projects future demand trajectory, stockout timelines, revenue loss at risk,
and indexes network-wide store surplus pools to enable cross-store transfers.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PredictorAgent:
    """Agent that projects demand runways and network inventory surplus pools."""

    name = "Predictor Agent"

    @classmethod
    def predict_trajectories(cls, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Project demand forward and build network transfer surplus map."""
        now = datetime.now(timezone.utc)
        predictions = []
        network_surplus_pool: Dict[str, List[Dict[str, Any]]] = {}

        for obs in observations:
            store_id = obs["store_id"]
            item_id = obs["item_id"]
            stock = obs["current_stock"]
            daily_demand = obs["daily_demand"]
            price = obs["unit_price"]
            lead_time = obs["lead_time_days"]
            days_of_stock = obs["days_of_stock"]

            # Projected stockout date
            if daily_demand > 0 and days_of_stock < 365:
                stockout_date = (now + timedelta(days=int(days_of_stock))).strftime("%Y-%m-%d")
            else:
                stockout_date = None

            # Revenue at risk if stocked out before lead time arrival
            if days_of_stock < lead_time and daily_demand > 0:
                gap_days = max(0.0, lead_time - days_of_stock)
                revenue_at_risk = round(gap_days * daily_demand * price, 2)
            else:
                revenue_at_risk = 0.0

            # Excess capital tied up (> 45 days of supply)
            optimal_stock = daily_demand * 28
            if stock > optimal_stock:
                excess_units = max(0, stock - optimal_stock)
                excess_capital = round(excess_units * price, 2)
                # Register in multi-store transfer pool
                if excess_units > 10:
                    network_surplus_pool.setdefault(item_id, []).append({
                        "store_id": store_id,
                        "surplus_units": int(excess_units),
                    })
            else:
                excess_units = 0
                excess_capital = 0.0

            pred = {
                **obs,
                "projected_stockout_date": stockout_date,
                "revenue_at_risk": revenue_at_risk,
                "excess_units": int(excess_units),
                "excess_capital_tied_up": excess_capital,
            }
            predictions.append(pred)

        logger.info(f"Predictor Agent analyzed {len(predictions)} items. Identified {len(network_surplus_pool)} surplus transfer pools.")
        return {
            "predictions": predictions,
            "network_surplus_pool": network_surplus_pool,
        }
