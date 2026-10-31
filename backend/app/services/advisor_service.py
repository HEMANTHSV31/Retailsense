"""AI Business Advisor — data-grounded Q&A over RetailIQ's real data.

Pipeline:
  1. Build a compact, structured "business snapshot" from the org's actual
     MySQL data (sales, inventory, forecasts, accuracy, alerts, weather).
  2. Send it to Claude (claude-opus-5) as context along with the user's
     question and prior conversation turns.
  3. Return the grounded answer.

If no ANTHROPIC_API_KEY is configured, falls back to a rule-based answer
built from the same snapshot so the advisor always responds.
"""

import json
import logging
from datetime import datetime, timezone

import pandas as pd

from app.core.config import settings
from app.services.data_service import TenantDataService
from app.services.purchase_engine import PurchaseDecisionEngine
from app.services.intelligence_service import IntelligenceService
from app.services.alert_service import AlertService
from app.services.model_registry_service import ModelRegistryService
from app.models.model_registry import ForecastAccuracy

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5"
MAX_SNAPSHOT_ITEMS = 12  # cap products/stores/alerts in the snapshot

SYSTEM_PROMPT = """You are the Senior Retail Decision Intelligence Advisor for RetailIQ.
You advise retail business owners, category managers, and supply chain directors.

Core Communication Rules:
1. Speak in polished, executive-ready, human-readable plain English.
2. Structure your answer with clear bold headings and clean bullet points:
   - **Executive Summary**: 1-2 sentence high-level takeaway.
   - **Data Findings & Situation**: Specific insights directly grounded in the provided snapshot (citing real store IDs, SKU names, revenue, days of stock, and unit counts).
   - **Recommended Next Actions**: Prioritized, actionable operational decisions (e.g. Purchase Orders, Inter-Store Transfers, Price Markdowns).
   - **Financial Bottom Line**: Net working capital freed, revenue protected, or holding cost reduction.
3. DO NOT output ASCII pipe tables (never use '| Col | Col |'). Instead, format tabular lists as clean bullet points with bold identifiers.
4. Ground every single claim in the business snapshot. Never fabricate numbers. If specific data is absent, state what needs to be verified."""



class AdvisorService:
    """Data-grounded Q&A for business owners and managers."""

    # ── Snapshot construction ───────────────────────────────────────────────

    @staticmethod
    async def build_snapshot(db, org) -> dict:
        """Gather the org's key metrics into a compact JSON context."""
        snapshot = {"organization": org.name, "generated_at": datetime.now(timezone.utc).isoformat()}

        sales_df = await TenantDataService.load_sales_df(db, org.id)
        if not sales_df.empty:
            snapshot["sales"] = AdvisorService._sales_summary(sales_df)

        inv_df = await TenantDataService.load_inventory_df(db, org.id)
        if not inv_df.empty:
            sales_df = sales_df.merge(inv_df, on=["item_id", "store_id"], how="left")
        if "current_stock" not in sales_df.columns or sales_df["current_stock"].isna().all():
            stock = sales_df.groupby(["item_id", "store_id"])["sales"].transform(lambda x: max(x.tail(28).sum() * 1.5, 10))
            sales_df = sales_df.copy()
            sales_df["current_stock"] = stock
        if not sales_df.empty:
            engine = PurchaseDecisionEngine()
            decisions = engine.generate_purchase_decisions(sales_df)
            if not decisions.empty:
                snapshot["inventory"] = {
                    "financials": engine.financial_summary(decisions),
                    "top_reorder_items": decisions.nlargest(MAX_SNAPSHOT_ITEMS, "recommended_order_qty")[
                        ["item_id", "store_id", "recommended_order_qty", "stockout_in_days",
                         "overstock_capital", "inventory_value", "days_of_stock"]
                    ].to_dict("records"),
                    "stockout_risks": decisions[decisions["stockout_in_days"].notna()][
                        ["item_id", "store_id", "stockout_in_days"]
                    ].head(MAX_SNAPSHOT_ITEMS).to_dict("records"),
                }

        # Store & product intelligence (top movers + underperformers)
        if not sales_df.empty:
            stores = IntelligenceService.all_stores_intelligence(sales_df)
            products = IntelligenceService.all_products_intelligence(sales_df)
            snapshot["stores"] = stores[:MAX_SNAPSHOT_ITEMS]
            snapshot["products"] = products[:MAX_SNAPSHOT_ITEMS]

        # Forecast accuracy + active model
        from sqlalchemy import select
        acc = (await db.execute(
            select(ForecastAccuracy).where(ForecastAccuracy.organization_id == org.id)
        )).scalars().all()
        if acc:
            snapshot["forecast_accuracy"] = [
                {"horizon_days": a.horizon_days, "wape": a.wape, "mae": a.mae, "points": a.eval_points}
                for a in acc[:MAX_SNAPSHOT_ITEMS]
            ]
        active = await ModelRegistryService.get_active(db, org.id)
        if active:
            snapshot["active_model"] = {
                "algorithm": active.algorithm, "version": active.version,
                "trained_at": active.trained_at.isoformat() if active.trained_at else None,
                "wape": active.wape, "live_wape": active.live_wape,
                "degraded": active.degradation_flagged,
            }

        # Alerts
        alerts = await AlertService.list_alerts(db, org.id, limit=MAX_SNAPSHOT_ITEMS)
        if alerts:
            snapshot["alerts"] = [
                {"type": a.alert_type.value, "severity": a.severity.value, "title": a.title}
                for a in alerts
            ]

        return snapshot

    @staticmethod
    def _sales_summary(df: pd.DataFrame) -> dict:
        daily = df.groupby("date")["sales"].sum()
        last_28 = daily.tail(28).sum()
        prior_28 = daily.iloc[-56:-28].sum()
        return {
            "total_products": int(df["item_id"].nunique()),
            "total_stores": int(df["store_id"].nunique()),
            "days_covered": int(df["date"].nunique()),
            "total_sales": round(float(df["sales"].sum()), 2),
            "avg_daily_sales": round(float(daily.mean()), 2),
            "last_28d_sales": round(float(last_28), 2),
            "prior_28d_sales": round(float(prior_28), 2),
            "growth_pct": round(float((last_28 - prior_28) / prior_28 * 100), 1) if prior_28 > 0 else None,
        }

    # ── Answering ───────────────────────────────────────────────────────────

    @staticmethod
    async def answer(db, org, user_id: str, question: str, history: list[dict] | None = None) -> dict:
        """Answer a business question grounded in the org's data."""
        snapshot = await AdvisorService.build_snapshot(db, org)

        if settings.GROQ_API_KEY:
            try:
                answer_text = await AdvisorService._groq_answer(snapshot, question, history or [])
                return {
                    "answer": answer_text,
                    "grounded": True,
                    "mode": f"groq ({settings.GROQ_MODEL})",
                    "snapshot_size": len(json.dumps(snapshot)),
                }
            except Exception as e:
                logger.error(f"Advisor Groq call failed, falling back: {e}")

        if settings.ANTHROPIC_API_KEY:
            try:
                answer_text = await AdvisorService._claude_answer(snapshot, question, history or [])
                return {
                    "answer": answer_text,
                    "grounded": True,
                    "mode": "claude",
                    "snapshot_size": len(json.dumps(snapshot)),
                }
            except Exception as e:
                logger.error(f"Advisor Claude call failed, falling back to rules: {e}")

        return {
            "answer": AdvisorService._rule_based_answer(question, snapshot),
            "grounded": True,
            "mode": "rules",
            "snapshot_size": len(json.dumps(snapshot)),
        }

    @staticmethod
    async def _groq_answer(snapshot: dict, question: str, history: list[dict]) -> str:
        """Call Groq API using gpt-oss-20b reasoning model."""
        import httpx
        context = json.dumps(snapshot, default=str)[:60_000]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in (history or [])[-6:]:
            role = "user" if turn.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": turn.get("content", "")})
        messages.append({"role": "user", "content": f"Business snapshot:\n{context}\n\nQuestion: {question}"})

        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": messages,
            "max_tokens": 1500,
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]["message"]
            content = choice.get("content") or ""
            if not content.strip() and choice.get("reasoning"):
                content = choice.get("reasoning")

            import re
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            return content.strip()

    @staticmethod
    async def _claude_answer(snapshot: dict, question: str, history: list[dict]) -> str:
        """Call Claude with the business snapshot as grounding context."""
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        context = json.dumps(snapshot, default=str)[:120_000]  # cap context size

        messages = []
        for turn in history[-6:]:  # last few turns of context
            role = "user" if turn.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": turn.get("content", "")})
        messages.append({"role": "user", "content": f"Business snapshot:\n{context}\n\nQuestion: {question}"})

        with client.messages.stream(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        if response.stop_reason == "refusal":
            return ("I'm not able to answer that from this business data. "
                    "Try asking about sales, inventory, forecasts, or store performance.")

        return next((b.text for b in response.content if b.type == "text"), "")

    # ── Rule-based fallback (no API key) ────────────────────────────────────

    @staticmethod
    def _rule_based_answer(question: str, snapshot: dict) -> str:
        """Answer common question types from the snapshot in polished executive format."""
        q = question.lower()
        sections = []

        sales = snapshot.get("sales", {})
        inv = snapshot.get("inventory", {})
        stores = snapshot.get("stores", [])
        products = snapshot.get("products", [])
        alerts = snapshot.get("alerts", [])

        if any(k in q for k in ["why", "declin", "drop", "down", "decreas"]):
            growth = sales.get("growth_pct")
            sections.append("### Sales Trend Analysis")
            if growth is not None and growth < 0:
                sections.append(f"Network sales experienced a **{abs(growth):.1f}% decline** over the recent cycle vs. prior period.")
            else:
                sections.append(f"Network demand is stable to positive (**+{growth:.1f}%** observed) across the recent observation window." if growth is not None else "Historical timeline is currently accumulating baseline data.")

            declining = [p for p in products if p.get("growth_pct") is not None and p["growth_pct"] < -10]
            if declining:
                sections.append("### Primary Demand Contributors\n" + "\n".join(f"- **{p['item_id']}**: Velocity dropped {p['growth_pct']:.1f}%" for p in declining[:5]))
            if alerts:
                sections.append("### Operational Signals\n" + "\n".join(f"- {a['title']} (*{a['severity']}*)" for a in alerts[:3]))

        elif any(k in q for k in ["reorder", "order", "stock up", "purchase", "buy"]):
            reorder = inv.get("top_reorder_items", [])
            sections.append("### Priority Purchase Directives")
            if reorder:
                sections.append("Immediate supplier replenishment recommended for high-velocity SKUs facing stockout:")
                for r in reorder[:5]:
                    stockout = r.get('stockout_in_days')
                    stockout_str = f" &bull; runs out in **{stockout:.0f} days**" if stockout is not None else ""
                    sections.append(f"- **{r['item_id']}** at **Store {r['store_id']}**: Reorder **+{r['recommended_order_qty']:.0f} units** (Current runway: {r.get('days_of_stock', 0):.0f}d{stockout_str})")
            else:
                sections.append("- No urgent stockouts detected across evaluated store inventory buffers.")

            if inv.get("financials"):
                f = inv["financials"]
                sections.append(f"### Financial Summary\n"
                                f"- **Total Inventory Value**: ${f['total_inventory_value']:,.2f}\n"
                                f"- **At-Risk Stockout Loss**: ${f['total_stockout_loss_risk']:,.2f}\n"
                                f"- **Excess Capital Tied Up**: ${f['total_overstock_capital']:,.2f}\n"
                                f"- **Potential Net Savings**: ${f['total_potential_savings']:,.2f}")

        elif any(k in q for k in ["store", "underperform", "perform", "branch", "location"]):
            sections.append("### Store Network Performance")
            if stores:
                best = sorted(stores, key=lambda s: s.get("total_sales", 0), reverse=True)[:3]
                worst = sorted(stores, key=lambda s: (s.get("growth_pct") or 0))[:3]
                sections.append("**Top Performing Locations:**\n" + "\n".join(f"- **Store {s['store_id']}**: ${s.get('total_sales',0):,.2f} revenue" for s in best))
                sections.append("**Locations Requiring Attention:**\n" + "\n".join(f"- **Store {s['store_id']}**: Growth {s.get('growth_pct', 0)}%" for s in worst if s.get("growth_pct") is not None))

        elif any(k in q for k in ["demand", "increase", "growth", "trend", "upcoming", "popular"]):
            growing = [p for p in products if p.get("growth_pct") is not None and p["growth_pct"] > 10]
            sections.append("### Rising Velocity Products")
            if growing:
                sections.append("Products demonstrating positive velocity acceleration:\n" + "\n".join(f"- **{p['item_id']}**: +{p['growth_pct']:.1f}% demand surge" for p in growing[:5]))
            else:
                sections.append("- Product sales volume is currently tracking near steady-state baseline.")

        else:
            sections.append("### Executive Business Overview")
            sections.append(f"RetailIQ is actively monitoring **{sales.get('total_products', 0)} active products** across **{sales.get('total_stores', 0)} stores** covering **{sales.get('total_sales', 0):,.0f} units** sold.")
            if inv.get("financials"):
                f = inv["financials"]
                sections.append(f"- **Network Inventory Value**: ${f.get('total_inventory_value', 0):,.2f}\n"
                                f"- **Stockout Risk Avoidance**: ${f.get('total_stockout_loss_risk', 0):,.2f}\n"
                                f"- **SKUs Requiring PO**: {f.get('items_to_reorder', 0)} items")

        return "\n\n".join(sections)


