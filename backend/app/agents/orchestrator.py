"""Agent Orchestrator — Coordinates the full Autonomous Retail Decision Intelligence Loop.

Observe -> Predict -> Reason -> Decide -> Act -> Measure

Manages execution lifecycle, step progress logging, and Groq reasoning enrichment.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import pandas as pd

from app.agents.observer_agent import ObserverAgent
from app.agents.predictor_agent import PredictorAgent
from app.agents.reasoner_agent import ReasonerAgent
from app.agents.decider_agent import DeciderAgent
from app.agents.measurer_agent import MeasurerAgent

logger = logging.getLogger(__name__)


class AnalysisRunStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentOrchestrator:
    """Coordinates the multi-agent graph execution."""

    # In-memory registry of run states for real-time progress stepper
    _runs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_run_status(cls, run_id: str) -> Optional[Dict[str, Any]]:
        return cls._runs.get(run_id)

    @classmethod
    def get_all_runs(cls) -> List[Dict[str, Any]]:
        return sorted(cls._runs.values(), key=lambda r: r.get("created_at", ""), reverse=True)

    @classmethod
    def get_latest_run(cls) -> Optional[Dict[str, Any]]:
        runs = cls.get_all_runs()
        return runs[0] if runs else None

    @classmethod
    async def trigger_analysis_run(
        cls,
        sales_df: pd.DataFrame,
        lead_time_days: int = 7,
        service_level: float = 0.95,
        enrich_top_with_groq: int = 3,
    ) -> str:
        """Launch autonomous multi-agent analysis in the background."""
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        cls._runs[run_id] = {
            "run_id": run_id,
            "status": AnalysisRunStatus.PENDING,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "current_step": 0,
            "total_steps": 5,
            "active_agent": "Initializing",
            "step_log": ["Initialized Decision Intelligence graph pipeline."],
            "result": None,
            "error": None,
        }

        # Run pipeline asynchronously
        asyncio.create_task(
            cls._execute_pipeline(
                run_id=run_id,
                sales_df=sales_df,
                lead_time_days=lead_time_days,
                service_level=service_level,
                enrich_top_with_groq=enrich_top_with_groq,
            )
        )
        return run_id

    @classmethod
    async def _execute_pipeline(
        cls,
        run_id: str,
        sales_df: pd.DataFrame,
        lead_time_days: int,
        service_level: float,
        enrich_top_with_groq: int,
    ):
        run = cls._runs[run_id]
        run["status"] = AnalysisRunStatus.RUNNING

        try:
            # ── Step 1: Observer Agent ─────────────────────────────
            run["current_step"] = 1
            run["active_agent"] = "Observer Agent"
            run["step_log"].append("Observer Agent: Ingesting sales, inventory, and supplier lead-time signals...")
            await asyncio.sleep(0.4)

            observations = ObserverAgent.observe(
                df=sales_df,
                lead_time_days=lead_time_days,
                service_level=service_level,
            )
            run["step_log"].append(f"Observer Agent: Classified {len(observations)} store-SKU nodes.")

            # ── Step 2: Predictor Agent ────────────────────────────
            run["current_step"] = 2
            run["active_agent"] = "Predictor Agent"
            run["step_log"].append("Predictor Agent: Calculating demand velocity, days of runway, and network surplus pools...")
            await asyncio.sleep(0.4)

            pred_bundle = PredictorAgent.predict_trajectories(observations)
            predictions = pred_bundle["predictions"]
            surplus_pool = pred_bundle["network_surplus_pool"]
            run["step_log"].append(f"Predictor Agent: Indexed {len(surplus_pool)} cross-store surplus transfer pools.")

            # ── Step 3: Decider Agent ──────────────────────────────
            run["current_step"] = 3
            run["active_agent"] = "Decider Agent"
            run["step_log"].append("Decider Agent: Selecting optimal business actions from 7 action levers...")
            await asyncio.sleep(0.4)

            decisions = DeciderAgent.decide_actions(predictions, surplus_pool)
            run["step_log"].append(f"Decider Agent: Generated {len(decisions)} actionable store decisions.")

            # ── Step 4: Reasoner Agent (Groq LLM) ──────────────────
            run["current_step"] = 4
            run["active_agent"] = "Groq Reasoner Agent"
            run["step_log"].append("Groq Reasoner Agent: Evaluating connected value-chain trade-offs (Demand -> Logistics -> Margin)...")

            # Enrich top critical/high urgency decisions with live Groq LLM
            critical_items = [d for d in decisions if d["urgency"] in ["CRITICAL", "HIGH"]][:enrich_top_with_groq]
            for d in critical_items:
                enriched_reason = await ReasonerAgent.enrich_with_groq(d, d["action"], d["tradeoff_chain"])
                d["rationale"] = enriched_reason
                d["is_enriched"] = True

            run["step_log"].append(f"Groq Reasoner Agent: Enriched {len(critical_items)} decisions using openai/gpt-oss-20b.")

            # ── Step 5: Measurer Agent ─────────────────────────────
            run["current_step"] = 5
            run["active_agent"] = "Measurer Agent"
            run["step_log"].append("Measurer Agent: Benchmarking AI system vs traditional Min-Max baseline...")
            await asyncio.sleep(0.3)

            benchmark = MeasurerAgent.benchmark_decisions(decisions)
            run["step_log"].append("Measurer Agent: Benchmark analysis computed successfully.")

            # Action Breakdown
            breakdown = {}
            for d in decisions:
                breakdown[d["action"]] = breakdown.get(d["action"], 0) + 1

            # Complete
            run["status"] = AnalysisRunStatus.COMPLETED
            run["active_agent"] = "Finished"
            run["completed_at"] = datetime.now(timezone.utc).isoformat()
            run["result"] = {
                "run_id": run_id,
                "total_decisions": len(decisions),
                "action_breakdown": breakdown,
                "baseline_comparison": benchmark,
                "decisions": decisions,
            }
            logger.info(f"Pipeline run {run_id} completed successfully.")

        except Exception as e:
            logger.error(f"Pipeline run {run_id} failed: {e}", exc_info=True)
            run["status"] = AnalysisRunStatus.FAILED
            run["error"] = str(e)
            run["step_log"].append(f"Pipeline Error: {e}")
