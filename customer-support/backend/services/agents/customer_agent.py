"""
Customer Persona Agent — LangGraph-powered customer simulator.
Generates realistic customer messages grounded in company knowledge.
Maintains emotional state that evolves based on agent quality.
"""
import logging
import json
from typing import TypedDict, Literal

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END

from config import OLLAMA_BASE_URL, LLM_MODEL, LLM_TEMPERATURE

logger = logging.getLogger(__name__)


class CustomerState(TypedDict):
    """State for the customer persona agent."""
    # Scenario context
    persona_name: str
    persona_description: str
    issue_description: str
    difficulty: str
    category: str
    company_context: str  # RAG-retrieved company knowledge

    # Conversation state
    messages: list[dict]  # Full conversation history
    current_emotional_state: str
    turn_count: int
    max_turns: int

    # Output
    customer_response: str
    is_resolved: bool


def _build_system_prompt(state: CustomerState) -> str:
    """Build the system prompt for the customer persona."""
    difficulty_instructions = {
        "easy": (
            "You are a patient and straightforward customer. You clearly describe your issue, "
            "respond well to helpful agents, and are easy to satisfy. Stay calm throughout."
        ),
        "medium": (
            "You are a somewhat frustrated customer. You may repeat yourself if the agent "
            "doesn't address your concern directly. You appreciate empathy but won't settle "
            "for generic answers. Show moderate frustration if help is inadequate."
        ),
        "hard": (
            "You are an extremely frustrated and demanding customer. You may be rude, "
            "interrupt, bring up past negative experiences, and threaten to cancel. "
            "You require exceptional empathy and precise solutions to calm down. "
            "Only de-escalate if the agent demonstrates genuine understanding and offers "
            "concrete solutions. You may escalate if the agent is dismissive."
        ),
    }

    emotional_transitions = {
        "angry": "You are currently ANGRY. You use short, sharp sentences. You may use caps for emphasis.",
        "frustrated": "You are currently FRUSTRATED. You express disappointment and may sigh or show exasperation.",
        "neutral": "You are currently NEUTRAL. You communicate normally and are open to solutions.",
        "satisfied": "You are currently SATISFIED. The agent is handling things well. You're becoming cooperative.",
        "happy": "You are currently HAPPY. The agent has been excellent. You may express gratitude.",
    }

    return f"""You are role-playing as a customer named {state['persona_name']}.

CHARACTER BACKGROUND:
{state['persona_description']}

YOUR ISSUE:
{state['issue_description']}

DIFFICULTY LEVEL ({state['difficulty'].upper()}):
{difficulty_instructions.get(state['difficulty'], difficulty_instructions['medium'])}

EMOTIONAL STATE:
{emotional_transitions.get(state['current_emotional_state'], emotional_transitions['neutral'])}

COMPANY CONTEXT (use this to make your queries realistic and specific):
{state['company_context']}

RULES:
1. Stay in character at ALL times. Never break the fourth wall.
2. React naturally to the agent's responses — if they're helpful, soften your tone; if dismissive, escalate.
3. Reference specific products, services, or policies from the company context when relevant.
4. Your messages should be 1-4 sentences long, like a real customer chat/call.
5. If your issue is genuinely resolved with a satisfactory answer, say something like "Thank you, that helps!" or "Great, I appreciate it."
6. Never say you are an AI or a simulation.
7. Respond ONLY with your customer message. No JSON, no metadata, no stage directions."""


def _build_emotion_evaluator_prompt(state: CustomerState) -> str:
    """Build prompt to evaluate emotional state after agent response."""
    return f"""Analyze the following customer support conversation and determine the customer's emotional state.

The customer ({state['persona_name']}) started as {state['current_emotional_state']}.
Difficulty level: {state['difficulty']}

Recent exchange:
{_format_recent_messages(state['messages'], last_n=4)}

Based on the agent's latest response quality, what is the customer's new emotional state?
Also determine if the customer's issue has been resolved.

Respond ONLY in this exact JSON format:
{{"emotional_state": "angry|frustrated|neutral|satisfied|happy", "is_resolved": true|false, "reason": "brief explanation"}}"""


def _format_recent_messages(messages: list[dict], last_n: int = 4) -> str:
    """Format recent messages for prompt context."""
    recent = messages[-last_n:] if len(messages) > last_n else messages
    formatted = []
    for msg in recent:
        role_label = "Customer" if msg["role"] == "customer" else "Support Agent"
        formatted.append(f"{role_label}: {msg['content']}")
    return "\n".join(formatted)


def _format_full_history(messages: list[dict]) -> str:
    """Format full conversation history for the LLM."""
    formatted = []
    for msg in messages:
        role_label = "Customer" if msg["role"] == "customer" else "Support Agent"
        formatted.append(f"{role_label}: {msg['content']}")
    return "\n".join(formatted)


def generate_customer_message(state: CustomerState) -> dict:
    """Generate a customer message based on current state."""
    llm = ChatOllama(
        model=LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=LLM_TEMPERATURE,
    )

    system_prompt = _build_system_prompt(state)

    # Build conversation context
    if state["messages"]:
        conversation = f"\nConversation so far:\n{_format_full_history(state['messages'])}\n\nNow respond as the customer:"
    else:
        conversation = "\nStart the conversation by describing your issue to the support agent:"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": conversation},
    ]

    response = llm.invoke(messages)
    customer_msg = response.content.strip()

    # Clean up any accidental metadata in response
    if customer_msg.startswith('"') and customer_msg.endswith('"'):
        customer_msg = customer_msg[1:-1]

    logger.info(f"Customer agent ({state['persona_name']}) generated message "
                f"[emotion: {state['current_emotional_state']}]")

    return {"customer_response": customer_msg}


def evaluate_emotional_state(state: CustomerState) -> dict:
    """Evaluate and update the customer's emotional state based on agent response."""
    if not state["messages"] or len(state["messages"]) < 2:
        return {
            "current_emotional_state": state["current_emotional_state"],
            "is_resolved": False,
        }

    llm = ChatOllama(
        model=LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,  # Low temperature for consistent evaluation
    )

    prompt = _build_emotion_evaluator_prompt(state)

    messages = [
        {"role": "system", "content": "You are an emotion analysis expert. Respond only in JSON format."},
        {"role": "user", "content": prompt},
    ]

    response = llm.invoke(messages)

    try:
        # Parse JSON response
        result_text = response.content.strip()
        # Handle potential markdown code block wrapping
        if "```" in result_text:
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        result = json.loads(result_text)
        new_state = result.get("emotional_state", state["current_emotional_state"])
        is_resolved = result.get("is_resolved", False)

        logger.info(f"Emotion evaluation: {state['current_emotional_state']} → {new_state}, "
                     f"resolved: {is_resolved}")

        return {
            "current_emotional_state": new_state,
            "is_resolved": is_resolved,
        }
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse emotion evaluation: {e}")
        return {
            "current_emotional_state": state["current_emotional_state"],
            "is_resolved": False,
        }


def should_continue(state: CustomerState) -> Literal["generate", "end"]:
    """Determine if the conversation should continue or end."""
    if state.get("is_resolved", False):
        return "end"
    if state["turn_count"] >= state["max_turns"]:
        return "end"
    return "generate"


def build_customer_graph() -> StateGraph:
    """Build the LangGraph state graph for customer persona simulation."""
    graph = StateGraph(CustomerState)

    # Add nodes
    graph.add_node("generate_message", generate_customer_message)
    graph.add_node("evaluate_emotion", evaluate_emotional_state)

    # Set entry point
    graph.set_entry_point("generate_message")

    # Add edges
    graph.add_edge("generate_message", "evaluate_emotion")
    graph.add_conditional_edges(
        "evaluate_emotion",
        should_continue,
        {
            "generate": "generate_message",
            "end": END,
        }
    )

    return graph.compile()


class CustomerAgent:
    """High-level interface for the customer persona simulation."""

    def __init__(self):
        self._graph = None

    def _ensure_graph(self):
        """Lazy initialization of the LangGraph."""
        if self._graph is None:
            self._graph = build_customer_graph()

    def generate_opening_message(self, persona_name: str, persona_description: str,
                                  issue_description: str, difficulty: str,
                                  category: str, company_context: str,
                                  max_turns: int = 20) -> dict:
        """Generate the customer's opening message."""
        state = CustomerState(
            persona_name=persona_name,
            persona_description=persona_description,
            issue_description=issue_description,
            difficulty=difficulty,
            category=category,
            company_context=company_context,
            messages=[],
            current_emotional_state="neutral" if difficulty == "easy" else "frustrated",
            turn_count=0,
            max_turns=max_turns,
            customer_response="",
            is_resolved=False,
        )

        result = generate_customer_message(state)
        return {
            "message": result["customer_response"],
            "emotional_state": state["current_emotional_state"],
        }

    def generate_response(self, persona_name: str, persona_description: str,
                          issue_description: str, difficulty: str,
                          category: str, company_context: str,
                          messages: list[dict], current_emotional_state: str,
                          max_turns: int = 20) -> dict:
        """Generate a customer response to the agent's message."""
        state = CustomerState(
            persona_name=persona_name,
            persona_description=persona_description,
            issue_description=issue_description,
            difficulty=difficulty,
            category=category,
            company_context=company_context,
            messages=messages,
            current_emotional_state=current_emotional_state,
            turn_count=len([m for m in messages if m["role"] == "customer"]),
            max_turns=max_turns,
            customer_response="",
            is_resolved=False,
        )

        # First evaluate how the agent's response affected emotions
        emotion_result = evaluate_emotional_state(state)
        state["current_emotional_state"] = emotion_result["current_emotional_state"]
        state["is_resolved"] = emotion_result["is_resolved"]

        if state["is_resolved"]:
            # Generate a closing/thank-you message
            result = generate_customer_message(state)
            return {
                "message": result["customer_response"],
                "emotional_state": state["current_emotional_state"],
                "is_resolved": True,
            }

        # Generate next customer message
        result = generate_customer_message(state)
        return {
            "message": result["customer_response"],
            "emotional_state": state["current_emotional_state"],
            "is_resolved": False,
        }


# Singleton instance
customer_agent = CustomerAgent()
