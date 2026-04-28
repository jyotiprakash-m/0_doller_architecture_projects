"""
Simulation Router — Training session management and real-time chat simulation.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from config import CREDIT_COST_SESSION, CREDIT_COST_SCENARIO_GEN, MAX_SIM_TURNS
from services import db
from services.auth_utils import get_current_user_id
from services.agents.orchestrator import orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/simulation", tags=["Training Simulation"])


class CreateScenarioRequest(BaseModel):
    persona_name: str
    persona_description: str
    issue_description: str
    difficulty: str = "medium"
    category: str = "general_inquiry"
    expected_resolution: str = ""
    initial_emotional_state: str = "neutral"
    kb_id: Optional[str] = None


class GenerateScenariosRequest(BaseModel):
    kb_id: str
    count: int = 3


class StartSessionRequest(BaseModel):
    scenario_id: str


class AgentResponseRequest(BaseModel):
    message: str


# --- Scenario Endpoints ---

@router.post("/scenarios/generate")
async def generate_scenarios(req: GenerateScenariosRequest,
                              user_id: str = Depends(get_current_user_id)):
    """Auto-generate scenarios from knowledge base content."""
    # Check credits
    credits = db.get_user_credits(user_id)
    if credits < CREDIT_COST_SCENARIO_GEN:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    # Verify KB ownership
    kb = db.get_knowledge_base(req.kb_id)
    if not kb or kb["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Generate scenarios
    scenarios = orchestrator.generate_scenarios(user_id, req.kb_id, count=req.count)

    # Save to database
    saved = []
    for s in scenarios:
        saved_scenario = db.create_scenario(
            user_id=user_id, kb_id=req.kb_id,
            persona_name=s["persona_name"],
            persona_description=s["persona_description"],
            issue_description=s["issue_description"],
            difficulty=s["difficulty"],
            category=s["category"],
            expected_resolution=s.get("expected_resolution", ""),
            initial_emotional_state=s.get("initial_emotional_state", "neutral"),
            is_auto_generated=True,
        )
        saved.append(saved_scenario)

    # Deduct credits
    db.update_user_credits(user_id, -CREDIT_COST_SCENARIO_GEN)

    logger.info(f"Generated {len(saved)} scenarios for KB {req.kb_id}")
    return {"scenarios": saved, "credits_remaining": db.get_user_credits(user_id)}


@router.get("/scenarios")
async def list_scenarios(kb_id: Optional[str] = None,
                         user_id: str = Depends(get_current_user_id)):
    """List available training scenarios."""
    return db.get_scenarios(user_id, kb_id=kb_id)


@router.post("/scenarios")
async def create_scenario(req: CreateScenarioRequest,
                           user_id: str = Depends(get_current_user_id)):
    """Manually create a training scenario."""
    scenario = db.create_scenario(
        user_id=user_id, kb_id=req.kb_id,
        persona_name=req.persona_name,
        persona_description=req.persona_description,
        issue_description=req.issue_description,
        difficulty=req.difficulty,
        category=req.category,
        expected_resolution=req.expected_resolution,
        initial_emotional_state=req.initial_emotional_state,
    )
    return scenario


@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a scenario."""
    scenario = db.get_scenario(scenario_id)
    if not scenario or scenario["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete_scenario(scenario_id)
    return {"status": "deleted"}


# --- Session Endpoints ---

@router.post("/start")
async def start_session(req: StartSessionRequest,
                         user_id: str = Depends(get_current_user_id)):
    """Start a new training session."""
    # Check credits
    credits = db.get_user_credits(user_id)
    if credits < CREDIT_COST_SESSION:
        raise HTTPException(status_code=402, detail="Insufficient credits for training session")

    # Get scenario
    scenario = db.get_scenario(req.scenario_id)
    if not scenario or scenario["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Create session
    session = db.create_training_session(user_id, req.scenario_id)

    # Generate opening customer message
    result = orchestrator.start_session(
        scenario=scenario, user_id=user_id,
        kb_id=scenario.get("kb_id"),
    )

    # Save customer message
    db.add_session_message(
        session_id=session["id"], role="customer",
        content=result["message"],
        emotional_state=result["emotional_state"],
    )

    # Deduct credits
    db.update_user_credits(user_id, -CREDIT_COST_SESSION)

    logger.info(f"Training session started: {session['id']}")

    return {
        "session": session,
        "customer_message": result["message"],
        "emotional_state": result["emotional_state"],
        "scenario": scenario,
        "credits_remaining": db.get_user_credits(user_id),
    }


@router.post("/{session_id}/respond")
async def agent_respond(session_id: str, req: AgentResponseRequest,
                         user_id: str = Depends(get_current_user_id)):
    """Submit trainee's response and get next customer message."""
    # Verify session
    session = db.get_training_session(session_id)
    if not session or session["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    # Check turn limit
    if session["message_count"] >= MAX_SIM_TURNS * 2:
        db.update_training_session(session_id, status="completed")
        raise HTTPException(status_code=400, detail="Maximum turns reached. Session completed.")

    # Get scenario
    scenario = db.get_scenario(session["scenario_id"])
    if not scenario:
        raise HTTPException(status_code=500, detail="Scenario not found")

    # Save agent message
    db.add_session_message(session_id=session_id, role="agent", content=req.message)

    # Get conversation history
    messages = db.get_session_messages(session_id)

    # Generate customer response
    result = orchestrator.process_agent_response(
        agent_message=req.message, scenario=scenario,
        messages=messages,
        current_emotional_state=session["current_emotional_state"],
        user_id=user_id, kb_id=scenario.get("kb_id"),
    )

    # Save customer response
    db.add_session_message(
        session_id=session_id, role="customer",
        content=result["message"],
        emotional_state=result["emotional_state"],
    )

    # Update session emotional state
    db.update_training_session(
        session_id, emotional_state=result["emotional_state"]
    )

    # Auto-complete if resolved
    if result.get("is_resolved"):
        db.update_training_session(session_id, status="completed")

    return {
        "customer_message": result["message"],
        "emotional_state": result["emotional_state"],
        "is_resolved": result.get("is_resolved", False),
        "session_status": "completed" if result.get("is_resolved") else "active",
    }


class SuggestionRequest(BaseModel):
    selected_doc_ids: list[str] = []

@router.post("/{session_id}/suggestions")
async def get_ai_suggestions(session_id: str, request: SuggestionRequest = SuggestionRequest(), user_id: str = Depends(get_current_user_id)):
    """Generate 3 AI suggested responses based on KB context."""
    session = db.get_training_session(session_id)
    if not session or session["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    scenario = db.get_scenario(session["scenario_id"])
    messages = db.get_session_messages(session_id)

    result = orchestrator.generate_suggestions(
        scenario=scenario, messages=messages,
        user_id=user_id, kb_id=scenario.get("kb_id"),
        selected_doc_ids=request.selected_doc_ids
    )

    return {"suggestions": result["suggestions"], "context": result["context"]}


@router.post("/{session_id}/end")
async def end_session(session_id: str, user_id: str = Depends(get_current_user_id)):
    """End a training session."""
    session = db.get_training_session(session_id)
    if not session or session["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    db.update_training_session(session_id, status="completed")

    return {"status": "completed", "session_id": session_id}


@router.get("/sessions")
async def list_sessions(status: Optional[str] = None,
                         user_id: str = Depends(get_current_user_id)):
    """List training sessions."""
    return db.get_training_sessions(user_id, status=status)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a training session with messages."""
    session = db.get_training_session(session_id)
    if not session or session["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.get_session_messages(session_id)
    scenario = db.get_scenario(session["scenario_id"])

    return {
        "session": session,
        "messages": messages,
        "scenario": scenario,
    }
