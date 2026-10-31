"""Autonomous Retail Decision Intelligence API endpoints.

Exposes:
  - GET /api/v1/decisions: Observe -> Predict -> Decide (generates multi-store actions and baseline comparison)
  - POST /api/v1/decisions/reason: Deep agentic reasoning using Groq (openai/gpt-oss-20b)
  - POST /api/v1/decisions/{decision_id}/execute: Act phase (execute/approve recommended action)
  - GET /api/v1/decisions/baseline: Measure phase (AI vs simple Min-Max baseline comparison)
"""

import os
import logging
from typing import Optional, Dict, Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_org
from app.models.user import User
from app.models.organization import Organization
from app.services.data_service import TenantDataService
from app.services.decision_engine import DecisionIntelligenceService

logger = logging.getLogger(__name__)

router = APIRouter()


class DecisionExecuteRequest(BaseModel):
    operator_notes: Optional[str] = None


class DecisionReasonRequest(BaseModel):
    decision: Dict[str, Any]


@router.get("")
async def get_decisions(
    lead_time_days: int = Query(7, ge=1, le=60),
    service_level: float = Query(0.95, ge=0.5, le=0.99),
    holding_cost_rate: float = Query(0.25, ge=0.01, le=1.0),
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full autonomous decision intelligence recommendations & baseline comparison."""
    df = await TenantDataService.load_sales_df(db, org.id)

    # If organization has no data uploaded yet, load sample test_upload.csv for demonstration
    if df.empty:
        candidate_paths = [
            os.path.join(os.getcwd(), "test_upload.csv"),
            os.path.join(os.getcwd(), "..", "test_upload.csv"),
            r"d:\TCSAI\RetailIQ\test_upload.csv",
        ]
        for p in candidate_paths:
            if os.path.exists(p):
                try:
                    df = pd.read_csv(p)
                    break
                except Exception as e:
                    logger.warning(f"Could not load fallback sample data from {p}: {e}")

    if df.empty:
        return DecisionIntelligenceService._empty_response()

    # Load real inventory if available
    inv_df = await TenantDataService.load_inventory_df(db, org.id)
    if not inv_df.empty:
        df = df.merge(inv_df, on=["item_id", "store_id"], how="left")

    result = DecisionIntelligenceService.generate_decisions_from_df(
        sales_df=df,
        lead_time_days=lead_time_days,
        service_level=service_level,
        holding_cost_rate=holding_cost_rate,
    )
    return result


@router.post("/reason")
async def enrich_decision_reasoning(
    payload: DecisionReasonRequest,
    current_user: User = Depends(get_current_user),
):
    """Invoke Groq LLM (openai/gpt-oss-20b) to provide multi-factor value-chain reasoning for a decision."""
    reasoning = await DecisionIntelligenceService.enrich_decision_with_llm(payload.decision)
    return {
        "decision_id": payload.decision.get("id"),
        "ai_rationale": reasoning,
    }


@router.post("/{decision_id}/execute")
async def execute_decision_action(
    decision_id: str,
    payload: DecisionExecuteRequest = None,
    current_user: User = Depends(get_current_user),
):
    """Execute / Approve an autonomous decision action (Act step)."""
    notes = payload.operator_notes if payload else None
    result = DecisionIntelligenceService.execute_action(decision_id=decision_id, operator_notes=notes)
    return result


@router.get("/baseline")
async def get_baseline_comparison(
    db: AsyncSession = Depends(get_db),
    org: Organization = Depends(get_current_org),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the AI vs. Naive Baseline benchmarking metrics."""
    decisions_resp = await get_decisions(db=db, org=org, current_user=current_user)
    return decisions_resp.get("baseline_comparison", {})

