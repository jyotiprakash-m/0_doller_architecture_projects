"""
Evaluation Router — Run AI evaluations and get feedback on training sessions.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends

from config import CREDIT_COST_EVALUATION
from services import db
from services.auth_utils import get_current_user_id
from services.agents.orchestrator import orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])


@router.post("/{session_id}")
async def run_evaluation(session_id: str, user_id: str = Depends(get_current_user_id)):
    """Run AI evaluation on a completed training session."""
    # Verify session
    session = db.get_training_session(session_id)
    if not session or session["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Session must be completed before evaluation")

    # Check if already evaluated
    existing = db.get_evaluation(session_id)
    if existing:
        return existing

    # Check credits
    credits = db.get_user_credits(user_id)
    if credits < CREDIT_COST_EVALUATION:
        raise HTTPException(status_code=402, detail="Insufficient credits for evaluation")

    # Get session data
    messages = db.get_session_messages(session_id)
    scenario = db.get_scenario(session["scenario_id"])
    if not scenario:
        raise HTTPException(status_code=500, detail="Scenario not found")

    # Run evaluation
    evaluation = orchestrator.evaluate_session(
        messages=messages, scenario=scenario,
        user_id=user_id, kb_id=scenario.get("kb_id"),
    )

    # Save evaluation
    saved = db.create_evaluation(
        session_id=session_id, user_id=user_id,
        overall_score=evaluation["overall_score"],
        empathy_score=evaluation["empathy_score"],
        accuracy_score=evaluation["accuracy_score"],
        resolution_score=evaluation["resolution_score"],
        communication_score=evaluation["communication_score"],
        feedback={"summary": evaluation.get("summary", "")},
        strengths=evaluation.get("strengths", []),
        improvements=evaluation.get("improvements", []),
        ideal_responses=evaluation.get("ideal_responses", []),
    )

    # Deduct credits
    db.update_user_credits(user_id, -CREDIT_COST_EVALUATION)

    logger.info(f"Evaluation saved for session {session_id}: {evaluation['overall_score']}/100")

    # Parse JSON fields for response
    result = db.get_evaluation(session_id)
    result["credits_remaining"] = db.get_user_credits(user_id)
    return result


@router.get("/{session_id}")
async def get_evaluation(session_id: str, user_id: str = Depends(get_current_user_id)):
    """Get evaluation results for a training session."""
    session = db.get_training_session(session_id)
    if not session or session["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    evaluation = db.get_evaluation(session_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="No evaluation found. Run evaluation first.")

    return evaluation


@router.get("/{session_id}/feedback")
async def get_feedback(session_id: str, user_id: str = Depends(get_current_user_id)):
    """Get personalized coaching feedback for a training session."""
    session = db.get_training_session(session_id)
    if not session or session["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    evaluation = db.get_evaluation(session_id)
    if not evaluation:
        raise HTTPException(status_code=400, detail="Run evaluation first")

    messages = db.get_session_messages(session_id)
    scenario = db.get_scenario(session["scenario_id"])

    feedback = orchestrator.generate_feedback(
        evaluation=evaluation, messages=messages,
        scenario=scenario, user_id=user_id,
        kb_id=scenario.get("kb_id") if scenario else None,
    )

    return feedback


@router.get("/history/all")
async def get_all_evaluations(user_id: str = Depends(get_current_user_id)):
    """Get all evaluations for the current user."""
    return db.get_user_evaluations(user_id)
