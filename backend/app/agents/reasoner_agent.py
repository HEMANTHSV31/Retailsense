"""Reasoner Agent — Step 3 of the Autonomous Decision Intelligence Loop.

Reasons over connected retail supply-chain tradeoffs across:
  Demand -> Inventory -> Replenishment -> Logistics -> Margin -> Customer Experience.
Powered by Groq LLM (openai/gpt-oss-20b) with deterministic fallback.
"""

import json
import logging
from typing import Dict, Any, List
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

REASONER_SYSTEM_PROMPT = """You are the Senior Retail Decision Intelligence Advisor.
Explain business decisions to retail executives and store managers in clear, polished, human-readable plain English.
Rules:
1. Speak directly and naturally in 2-3 coherent sentences.
2. Do NOT output headings, labels, asterisks like '**Executive Rationale**', bullet points, or raw JSON.
3. Clearly state the inventory threat, the specific action recommended, and the financial margin benefit."""


class ReasonerAgent:
    """Agent that performs multi-objective trade-off reasoning."""

    name = "Reasoner Agent"

    @classmethod
    def synthesize_tradeoff_chain(cls, item: Dict[str, Any], action: str, donor_store: str = None) -> Dict[str, str]:
        """Synthesize deterministic value-chain impacts across the 6 dimensions."""
        daily = item["daily_demand"]
        stock = item["current_stock"]
        days = item["days_of_stock"]
        price = item["unit_price"]
        lead = item["lead_time_days"]

        if action == "TRANSFER_INVENTORY":
            return {
                "demand": f"Active customer velocity of {daily} units/day.",
                "inventory": f"Depleted to {stock} units ({days} days remaining).",
                "replenishment": f"Supplier lead time ({lead}d) is too slow; internal transfer bridges the gap.",
                "logistics": f"Route transfer from sister store {donor_store} via regional shuttle (48h transit).",
                "margin": f"Protects full gross margin at ${price}/unit against a $15 flat freight cost.",
                "customer_experience": "Prevents immediate stockout and preserves on-shelf brand trust.",
            }
        elif action == "MARKDOWN":
            return {
                "demand": "Stagnant consumer velocity requiring price elasticity intervention.",
                "inventory": f"Overstock of {item.get('excess_units', 0)} units consuming warehouse capacity.",
                "replenishment": "Freeze supplier purchase orders immediately for this SKU.",
                "logistics": "Zero inter-store movement; liquidate directly on current sales floor.",
                "margin": "Accepts 20%-25% price concession to salvage working capital before holding cost erodes margin.",
                "customer_experience": "Draws bargain shoppers and clears space for higher-velocity seasonal items.",
            }
        elif action == "INCREASE_ALLOCATION":
            return {
                "demand": f"High sustained velocity ({daily} units/day) with seasonal upward momentum.",
                "inventory": "Safety stock will be compromised without priority replenishment.",
                "replenishment": "Elevate DC priority ranking to allocate 40% more volume to this location.",
                "logistics": "Optimize with full pallet replenishment to reduce unit transportation costs.",
                "margin": "Maximizes top-line revenue on high-margin anchor product.",
                "customer_experience": "Guarantees 100% on-shelf availability during peak traffic periods.",
            }
        elif action == "ADJUST_PROMOTION":
            return {
                "demand": "Demand response expected from targeted cross-merchandising circular.",
                "inventory": f"Supply runway of {days} days exceeds optimal 28-day target.",
                "replenishment": "Pause upcoming purchase order batch until stock velocity normalizes.",
                "logistics": "No emergency shipments needed.",
                "margin": "Protects unit price integrity through bundling instead of permanent discount.",
                "customer_experience": "Delivers perceived value without cheapening product line.",
            }
        elif action == "SUBSTITUTE_PRODUCT":
            return {
                "demand": "Shopper intent active at shelf facing.",
                "inventory": f"Primary SKU depleted ({stock} units).",
                "replenishment": "Emergency PO dispatched to supplier.",
                "logistics": "Supplier delivery in progress.",
                "margin": "Captures customer basket value on alternative high-margin SKU.",
                "customer_experience": "Minimizes friction by directing customers to exact functional substitute.",
            }
        elif action == "REPLENISH":
            return {
                "demand": f"Consistent sales rate of {daily} units/day.",
                "inventory": f"Stock ({stock} units) approaching reorder threshold ({item.get('reorder_point', 0)}).",
                "replenishment": "Issue standard purchase order to primary supplier.",
                "logistics": "Consolidate with scheduled weekly delivery route.",
                "margin": "Avoids emergency air-freight premiums.",
                "customer_experience": "Ensures seamless replenishment before stockout occurs.",
            }
        else:
            return {
                "demand": "Demand is stable and within expected statistical variance.",
                "inventory": f"Healthy safety buffer of {days} days covers operations.",
                "replenishment": "Maintain standard scheduled cadence.",
                "logistics": "No expedited logistics required.",
                "margin": "Operating at target margin with minimal holding cost.",
                "customer_experience": "High availability maintained effortlessly.",
            }

    @classmethod
    async def enrich_with_groq(cls, item: Dict[str, Any], action: str, tradeoff: Dict[str, str]) -> str:
        """Call Groq API (openai/gpt-oss-20b) for deep LLM reasoning."""
        if not settings.GROQ_API_KEY:
            return cls._fallback_rationale(action, item, tradeoff)

        prompt = (
            f"Analyze this retail decision:\n"
            f"- Store: {item.get('store_id')}, SKU: {item.get('item_id')}\n"
            f"- Recommended Action: {action}\n"
            f"- Current Stock: {item.get('current_stock')}, Daily Sales: {item.get('daily_demand')}\n"
            f"- Runway: {item.get('days_of_stock')} days, Unit Price: ${item.get('unit_price')}\n"
            f"- Trade-offs: {json.dumps(tradeoff)}\n\n"
            f"Explain in 2-3 sentences the strategic business rationale across Demand, Logistics, Margin, and Customer Experience."
        )

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": REASONER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 500,
            "temperature": 0.2,
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choice = data["choices"][0]["message"]
                    content = (choice.get("content") or "").strip()
                    if not content and choice.get("reasoning"):
                        content = choice.get("reasoning").strip()
                    if content:
                        for prefix in ["**Executive Rationale**", "Executive Rationale:", "**Rationale:**", "Rationale:"]:
                            content = content.replace(prefix, "")
                        return content.strip()
        except Exception as e:
            logger.warning(f"Groq Reasoning fallback: {e}")

        return cls._fallback_rationale(action, item, tradeoff)

    @classmethod
    def _fallback_rationale(cls, action: str, item: Dict[str, Any], tradeoff: Dict[str, str]) -> str:
        return f"{tradeoff.get('inventory', '')} {tradeoff.get('replenishment', '')} {tradeoff.get('margin', '')}"
