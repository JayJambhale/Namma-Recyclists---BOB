"""
routes.py — API routes + LangGraph agentic audit pipeline.

LangGraph graph: validate_weight → check_segregation → approve_or_reject
Each node is a pure Python function. When OPENAI_API_KEY is set, the
approve_or_reject node calls GPT-4o-mini for a one-sentence reasoning;
otherwise it falls back to a deterministic mock.
"""

import os
from datetime import datetime, timezone
from typing import TypedDict

from fastapi import APIRouter, HTTPException
from models import (
    Batch,
    MintRequest,
    MintResponse,
    NodeEvent,
    NodeStatus,
    NodeType,
    Property,
    WasteType,
)

# ── LangGraph imports ─────────────────────────────────────────────────────────
from langgraph.graph import END, StateGraph

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
#  LangGraph: Agentic Audit Pipeline
# ══════════════════════════════════════════════════════════════════════════════

class AuditState(TypedDict):
    """State passed through every audit node."""
    weight_kg: float
    waste_type: str
    node_type: str
    location: str
    weight_ok: bool
    segregation_ok: bool
    audit_passed: bool
    credits: float
    reasoning: str


# ── Node 1: Weight Validation ──────────────────────────────────────────────────
def validate_weight(state: AuditState) -> AuditState:
    """
    Rule: a single household pickup must be between 0.1 kg and 150 kg.
    Commercial batches may go up to 500 kg.
    """
    w = state["weight_kg"]
    upper = 500.0 if "Commercial" in state.get("location", "") else 150.0
    state["weight_ok"] = 0.1 <= w <= upper
    return state


# ── Node 2: Segregation Check ─────────────────────────────────────────────────
def check_segregation(state: AuditState) -> AuditState:
    """
    Rule: Sanitary and Special Care waste must arrive at DWCC, not directly
    to a Recycler (which would indicate mis-routing).
    """
    mis_routed = (
        state["waste_type"] in (WasteType.SANITARY, WasteType.SPECIAL_CARE)
        and state["node_type"] == NodeType.RECYCLER
    )
    state["segregation_ok"] = not mis_routed
    return state


# ── Node 3: Approve / Reject with optional LLM reasoning ─────────────────────
def approve_or_reject(state: AuditState) -> AuditState:
    passed = state["weight_ok"] and state["segregation_ok"]
    state["audit_passed"] = passed

    if passed:
        # Green Credit formula: weight × stream multiplier
        multipliers = {
            WasteType.DRY: 3.0,
            WasteType.WET: 1.5,
            WasteType.SANITARY: 2.0,
            WasteType.SPECIAL_CARE: 4.0,
        }
        m = multipliers.get(state["waste_type"], 1.5)
        state["credits"] = round(state["weight_kg"] * m, 2)
    else:
        state["credits"] = 0.0

    # Attempt LLM reasoning (graceful fallback if no key)
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and not openai_key.startswith("sk-replace"):
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_key)
            prompt = (
                f"Briefly explain (1 sentence) why this SWM batch audit "
                f"{'PASSED' if passed else 'FAILED'}. "
                f"Weight: {state['weight_kg']} kg, "
                f"Waste type: {state['waste_type']}, "
                f"Node: {state['node_type']}, "
                f"Weight OK: {state['weight_ok']}, "
                f"Segregation OK: {state['segregation_ok']}."
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            state["reasoning"] = response.content.strip()
        except Exception as exc:
            state["reasoning"] = f"[LLM unavailable: {exc}] Deterministic audit applied."
    else:
        # Deterministic fallback reasoning
        if passed:
            state["reasoning"] = (
                f"Batch passed: weight {state['weight_kg']} kg is within range "
                f"and waste type '{state['waste_type']}' is correctly routed to "
                f"'{state['node_type']}'."
            )
        else:
            reasons = []
            if not state["weight_ok"]:
                reasons.append(f"weight {state['weight_kg']} kg is out of range")
            if not state["segregation_ok"]:
                reasons.append(
                    f"'{state['waste_type']}' waste mis-routed to '{state['node_type']}'"
                )
            state["reasoning"] = "Batch FAILED audit: " + "; ".join(reasons) + "."

    return state


# ── Build the LangGraph workflow ───────────────────────────────────────────────
def _build_audit_graph() -> StateGraph:
    g = StateGraph(AuditState)
    g.add_node("validate_weight", validate_weight)
    g.add_node("check_segregation", check_segregation)
    g.add_node("approve_or_reject", approve_or_reject)

    g.set_entry_point("validate_weight")
    g.add_edge("validate_weight", "check_segregation")
    g.add_edge("check_segregation", "approve_or_reject")
    g.add_edge("approve_or_reject", END)
    return g.compile()


_audit_graph = _build_audit_graph()


# ══════════════════════════════════════════════════════════════════════════════
#  REST Endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/properties", tags=["Properties"])
async def list_properties():
    """Return all registered properties (for the dashboard selector)."""
    props = await Property.find_all().to_list()
    return [p.model_dump() for p in props]


@router.get("/properties/{property_id}", tags=["Properties"])
async def get_property(property_id: str):
    prop = await Property.find_one(Property.property_id == property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop.model_dump()


@router.get("/lineage/{property_id}", tags=["Lineage"])
async def get_lineage(property_id: str):
    """
    Fetch the most recent Batch document for a property.
    Returns the full embedded NodeEvent lineage for the timeline UI.
    """
    prop = await Property.find_one(Property.property_id == property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    batch = await (
        Batch.find(Batch.property_id == property_id)
        .sort(-Batch.collected_on)
        .first_or_none()
    )
    if not batch:
        raise HTTPException(
            status_code=404,
            detail=f"No batches found for property {property_id}",
        )

    return {
        "property": prop.model_dump(),
        "batch": batch.model_dump(),
    }


@router.post("/ledger/mint", response_model=MintResponse, tags=["Ledger"])
async def mint_credits(payload: MintRequest):
    """
    Webhook: receives a verified node event, runs the LangGraph audit,
    mints Green Credits, and appends the NodeEvent to the Batch lineage.
    """
    # 1. Validate property exists
    prop = await Property.find_one(Property.property_id == payload.property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # 2. Run LangGraph agentic audit
    initial_state: AuditState = {
        "weight_kg": payload.weight_kg,
        "waste_type": payload.waste_type,
        "node_type": payload.node_type,
        "location": payload.location,
        "weight_ok": False,
        "segregation_ok": False,
        "audit_passed": False,
        "credits": 0.0,
        "reasoning": "",
    }
    final_state: AuditState = _audit_graph.invoke(initial_state)

    # 3. Build NodeEvent
    new_event = NodeEvent(
        timestamp=datetime.now(timezone.utc),
        node_type=payload.node_type,
        location=payload.location,
        weight_kg=payload.weight_kg,
        status=NodeStatus.VERIFIED if final_state["audit_passed"] else NodeStatus.CONTAMINATED,
        operator_id=payload.operator_id,
        notes=final_state["reasoning"],
    )

    # 4. Upsert Batch — append event or create new batch
    batch = await Batch.find_one(Batch.batch_id == payload.batch_id)
    if batch:
        batch.events.append(new_event)
        if final_state["audit_passed"]:
            batch.is_audit_passed = True
            batch.credits_minted += final_state["credits"]
        await batch.save()
    else:
        batch = Batch(
            batch_id=payload.batch_id,
            property_id=payload.property_id,
            waste_type=payload.waste_type,
            initial_weight_kg=payload.weight_kg,
            events=[new_event],
            is_audit_passed=final_state["audit_passed"],
            credits_minted=final_state["credits"],
        )
        await batch.insert()

    # 5. Update property balance
    if final_state["audit_passed"] and final_state["credits"] > 0:
        prop.green_credits_balance = round(
            prop.green_credits_balance + final_state["credits"], 2
        )
        prop.total_waste_diverted_kg = round(
            prop.total_waste_diverted_kg + payload.weight_kg, 2
        )
        prop.segregation_streak_days += 1
        await prop.save()

    return MintResponse(
        batch_id=batch.batch_id,
        audit_passed=final_state["audit_passed"],
        credits_minted=final_state["credits"],
        new_balance=prop.green_credits_balance,
        audit_reasoning=final_state["reasoning"],
    )
