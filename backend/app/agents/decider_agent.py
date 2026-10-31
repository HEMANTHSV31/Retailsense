"""Decider Agent — Step 4 of the Autonomous Decision Intelligence Loop.

Arbitrates between alternative actions across the 7 required business levers:
  1. REPLENISH
  2. TRANSFER_INVENTORY
  3. INCREASE_ALLOCATION
  4. MARKDOWN
  5. ADJUST_PROMOTION
  6. SUBSTITUTE_PRODUCT
  7. TAKE_NO_ACTION
Assigns concrete execution parameters and urgency levels.
"""

import logging
from typing import Dict, Any, List
from app.agents.reasoner_agent import ReasonerAgent

logger = logging.getLogger(__name__)


class DeciderAgent:
    """Agent that determines what specific action each store or channel should take next."""

    name = "Decider Agent"

    @classmethod
    def decide_actions(
        cls,
        predictions: List[Dict[str, Any]],
        network_surplus_pool: Dict[str, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Map predictions and network pools into concrete, actionable retail decisions."""
        decisions = []

        for item in predictions:
            store_id = item["store_id"]
            item_id = item["item_id"]
            days_of_stock = item["days_of_stock"]
            lead_time = item["lead_time_days"]
            daily_demand = item["daily_demand"]
            price = item["unit_price"]
            stock = item["current_stock"]
            reorder_point = item["reorder_point"]

            decision_id = f"DEC-{abs(hash(store_id + item_id)) % 1000000:06d}"
            action = "TAKE_NO_ACTION"
            urgency = "LOW"
            confidence = 0.95
            parameters = {}
            donor_store = None

            # ── 1. Stockout Risk Arbitrage ─────────────────────────
            if days_of_stock <= lead_time:
                # Check cross-store transfer possibility
                donors = [d for d in network_surplus_pool.get(item_id, []) if d["store_id"] != store_id and d["surplus_units"] > 10]
                if donors:
                    action = "TRANSFER_INVENTORY"
                    donor_store = donors[0]["store_id"]
                    transfer_qty = min(donors[0]["surplus_units"], int(reorder_point - stock + 10))
                    urgency = "CRITICAL" if days_of_stock <= 2 else "HIGH"
                    confidence = 0.94
                    parameters = {
                        "source_store_id": donor_store,
                        "target_store_id": store_id,
                        "transfer_qty": transfer_qty,
                        "transit_time_days": 2,
                        "freight_cost": 15.0,
                    }
                elif days_of_stock <= 2:
                    action = "SUBSTITUTE_PRODUCT"
                    urgency = "CRITICAL"
                    confidence = 0.89
                    parameters = {
                        "substitute_item_id": f"SUB-{item_id}",
                        "interim_days": lead_time,
                        "emergency_reorder_qty": int(max(20, (reorder_point - stock) + daily_demand * 14)),
                    }
                else:
                    action = "REPLENISH"
                    urgency = "HIGH"
                    confidence = 0.92
                    parameters = {
                        "recommended_order_qty": int(max(20, (reorder_point - stock) + daily_demand * 14)),
                        "supplier_lead_time": lead_time,
                        "reorder_point": reorder_point,
                    }

            # ── 2. Excess / Overstock Arbitrage ─────────────────────
            elif days_of_stock > 60:
                excess_units = item.get("excess_units", 0)
                if daily_demand < 0.5:
                    action = "MARKDOWN"
                    urgency = "HIGH" if days_of_stock > 90 else "MEDIUM"
                    confidence = 0.91
                    discount_pct = 25
                    parameters = {
                        "markdown_pct": discount_pct,
                        "original_price": price,
                        "promotional_price": round(price * (1 - discount_pct / 100), 2),
                        "clearance_target_units": excess_units,
                    }
                else:
                    action = "ADJUST_PROMOTION"
                    urgency = "MEDIUM"
                    confidence = 0.88
                    parameters = {
                        "promo_strategy": "ENDCAP_BUNDLE_PROMOTION",
                        "target_lift_pct": 35,
                        "target_days_of_stock": 25,
                    }

            # ── 3. High Growth Spike Arbitrage ──────────────────────
            elif daily_demand > 5.0 and days_of_stock < 18:
                action = "INCREASE_ALLOCATION"
                urgency = "HIGH"
                confidence = 0.93
                parameters = {
                    "allocation_boost_pct": 40,
                    "target_weekly_units": round(daily_demand * 7 * 1.4, 1),
                }

            # ── 4. Equilibrium ──────────────────────────────────────
            else:
                action = "TAKE_NO_ACTION"
                urgency = "LOW"
                confidence = 0.98
                parameters = {"review_schedule_days": 7}

            # Build Connected Trade-off Chain
            tradeoff = ReasonerAgent.synthesize_tradeoff_chain(item, action, donor_store)
            rationale = ReasonerAgent._fallback_rationale(action, item, tradeoff)

            decisions.append({
                "id": decision_id,
                "store_id": store_id,
                "item_id": item_id,
                "category": item.get("category", "General"),
                "action": action,
                "urgency": urgency,
                "confidence_score": confidence,
                "signals": {
                    "current_stock": stock,
                    "days_of_stock": days_of_stock,
                    "daily_velocity": daily_demand,
                    "unit_price": price,
                    "lead_time_days": lead_time,
                },
                "parameters": parameters,
                "tradeoff_chain": tradeoff,
                "rationale": rationale,
                "expected_impact": {
                    "stockout_prevented": action in ["TRANSFER_INVENTORY", "SUBSTITUTE_PRODUCT", "REPLENISH", "INCREASE_ALLOCATION"],
                    "financial_gain": round(item.get("revenue_at_risk", 0.0) or item.get("excess_capital_tied_up", 0.0) * 0.4, 2),
                    "service_level_delta": "+12%" if urgency in ["CRITICAL", "HIGH"] else "0%",
                },
                "is_executed": False,
            })

        logger.info(f"Decider Agent generated {len(decisions)} action recommendations.")
        return decisions
