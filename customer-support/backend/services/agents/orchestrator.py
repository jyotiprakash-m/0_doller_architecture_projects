"""
Agent Orchestrator — Coordinates multi-agent workflows for training sessions.
Manages the flow: Scenario → Customer Simulation ↔ Agent Response → Evaluation → Feedback
"""
import logging
from services.agents.customer_agent import customer_agent
from services.agents.evaluator_agent import evaluator_agent
from services.agents.feedback_agent import feedback_agent
from services.agents.scenario_generator import scenario_generator
from services.agents.suggestion_agent import suggestion_agent
from services.rag_engine import rag_engine

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Central coordinator for all agent workflows."""

    def generate_scenarios(self, user_id: str, kb_id: str, count: int = 3) -> list[dict]:
        """Generate training scenarios from knowledge base content."""
        company_context = rag_engine.get_context(
            "Describe all products, services, policies, FAQs, and common customer issues.",
            user_id=user_id, kb_id=kb_id, top_k=5,
        )
        return scenario_generator.generate_scenarios(company_context, count=count)

    def start_session(self, scenario: dict, user_id: str, kb_id: str = None) -> dict:
        """Start a training session — generate the customer's opening message."""
        company_context = ""
        if kb_id:
            company_context = rag_engine.get_context(
                f"Information about: {scenario.get('issue_description', 'general inquiry')}",
                user_id=user_id, kb_id=kb_id, top_k=3,
            )
        result = customer_agent.generate_opening_message(
            persona_name=scenario["persona_name"],
            persona_description=scenario["persona_description"],
            issue_description=scenario["issue_description"],
            difficulty=scenario.get("difficulty", "medium"),
            category=scenario.get("category", "general_inquiry"),
            company_context=company_context,
        )
        logger.info(f"Session started — Persona: {scenario['persona_name']}, "
                     f"Difficulty: {scenario.get('difficulty', 'medium')}")
        return result

    def process_agent_response(self, agent_message: str, scenario: dict,
                                messages: list[dict], current_emotional_state: str,
                                user_id: str, kb_id: str = None) -> dict:
        """Process the trainee's response and generate the next customer message."""
        company_context = ""
        if kb_id:
            company_context = rag_engine.get_context(
                f"Information about: {scenario.get('issue_description', '')}",
                user_id=user_id, kb_id=kb_id, top_k=3,
            )
        # Add the agent's message to history
        full_messages = messages + [{"role": "agent", "content": agent_message}]
        result = customer_agent.generate_response(
            persona_name=scenario["persona_name"],
            persona_description=scenario["persona_description"],
            issue_description=scenario["issue_description"],
            difficulty=scenario.get("difficulty", "medium"),
            category=scenario.get("category", "general_inquiry"),
            company_context=company_context,
            messages=full_messages,
            current_emotional_state=current_emotional_state,
        )
        return result

    def evaluate_session(self, messages: list[dict], scenario: dict,
                         user_id: str, kb_id: str = None) -> dict:
        """Run full evaluation on a completed training session."""
        company_context = ""
        if kb_id:
            company_context = rag_engine.get_context(
                f"Complete information about: {scenario.get('issue_description', '')} "
                f"including policies, procedures, and correct answers.",
                user_id=user_id, kb_id=kb_id, top_k=5,
            )
        evaluation = evaluator_agent.evaluate_session(
            messages=messages,
            persona_name=scenario["persona_name"],
            category=scenario.get("category", "general_inquiry"),
            difficulty=scenario.get("difficulty", "medium"),
            issue_description=scenario.get("issue_description", ""),
            company_context=company_context,
        )
        logger.info(f"Evaluation complete — Overall: {evaluation['overall_score']}")
        return evaluation

    def generate_feedback(self, evaluation: dict, messages: list[dict],
                          scenario: dict, user_id: str, kb_id: str = None) -> dict:
        """Generate personalized coaching feedback."""
        company_context = ""
        if kb_id:
            company_context = rag_engine.get_context(
                f"Best practices and correct procedures for: {scenario.get('issue_description', '')}",
                user_id=user_id, kb_id=kb_id, top_k=3,
            )
        feedback = feedback_agent.generate_feedback(
            evaluation=evaluation, messages=messages,
            persona_name=scenario["persona_name"],
            category=scenario.get("category", "general_inquiry"),
            difficulty=scenario.get("difficulty", "medium"),
            company_context=company_context,
        )
        logger.info(f"Feedback generated — Recommendation: {feedback['difficulty_recommendation']}")
        return feedback

    def generate_suggestions(self, scenario: dict, messages: list[dict],
                             user_id: str, kb_id: str = None, selected_doc_ids: list[str] = None) -> list[dict]:
        """Generate 3 suggested replies for the executive based on KB context."""
        company_context = ""
        if kb_id or selected_doc_ids:
            # Query the latest customer message against the RAG
            last_msg = messages[-1]["content"] if messages else scenario.get("issue_description", "")
            company_context = rag_engine.get_context(
                f"How to respond to: {last_msg}",
                user_id=user_id, kb_id=kb_id, doc_ids=selected_doc_ids, top_k=3,
            )
        
        suggestions = suggestion_agent.generate_suggestions(
            persona_name=scenario["persona_name"],
            issue_description=scenario["issue_description"],
            messages=messages,
            company_context=company_context
        )
        return {
            "suggestions": suggestions,
            "context": company_context
        }


# Singleton
orchestrator = AgentOrchestrator()
