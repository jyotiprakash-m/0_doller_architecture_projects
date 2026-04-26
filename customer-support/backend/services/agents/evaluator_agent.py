"""
Evaluator Agent — Analyzes trainee agent responses and provides scored assessments.
Uses RAG to verify factual accuracy against company knowledge.
"""
import logging
import json

from langchain_ollama import ChatOllama

from config import OLLAMA_BASE_URL, LLM_MODEL

logger = logging.getLogger(__name__)


EVALUATION_PROMPT = """You are an expert customer support quality evaluator. Analyze the following training session conversation between a customer and a support agent trainee.

SCENARIO CONTEXT:
- Customer Persona: {persona_name}
- Issue Category: {category}
- Difficulty: {difficulty}
- Issue: {issue_description}

COMPANY KNOWLEDGE BASE CONTEXT:
{company_context}

FULL CONVERSATION TRANSCRIPT:
{transcript}

EVALUATE the support agent's performance on these dimensions (score 0-100 for each):

1. **EMPATHY** (0-100): Did the agent acknowledge the customer's feelings? Show understanding? Use appropriate tone? Personalize responses?

2. **ACCURACY** (0-100): Were the agent's answers factually correct based on the company knowledge? Did they provide accurate information about products/policies/procedures?

3. **RESOLUTION** (0-100): Did the agent address the core issue? Provide clear next steps? Work toward a resolution? Follow proper procedures?

4. **COMMUNICATION** (0-100): Was the agent clear and professional? Good grammar? Appropriate language? Well-structured responses?

Also identify:
- Top 3 STRENGTHS (specific things the agent did well, with quotes)
- Top 3 AREAS FOR IMPROVEMENT (specific things to work on, with quotes)
- For each agent message, suggest an IDEAL response that would score 95+

Respond ONLY in this exact JSON format:
{{
    "empathy_score": <0-100>,
    "accuracy_score": <0-100>,
    "resolution_score": <0-100>,
    "communication_score": <0-100>,
    "overall_score": <0-100>,
    "strengths": [
        {{"point": "description", "quote": "relevant agent quote"}},
        {{"point": "description", "quote": "relevant agent quote"}},
        {{"point": "description", "quote": "relevant agent quote"}}
    ],
    "improvements": [
        {{"point": "description", "quote": "relevant agent quote", "suggestion": "how to improve"}},
        {{"point": "description", "quote": "relevant agent quote", "suggestion": "how to improve"}},
        {{"point": "description", "quote": "relevant agent quote", "suggestion": "how to improve"}}
    ],
    "ideal_responses": [
        {{"agent_said": "what the agent actually said", "ideal": "what would have been better"}}
    ],
    "summary": "2-3 sentence overall assessment"
}}"""


def _format_transcript(messages: list[dict]) -> str:
    """Format session messages into a readable transcript."""
    lines = []
    for msg in messages:
        role = "CUSTOMER" if msg["role"] == "customer" else "AGENT"
        emotion = f" [{msg.get('emotional_state', '')}]" if msg.get("emotional_state") else ""
        lines.append(f"{role}{emotion}: {msg['content']}")
    return "\n\n".join(lines)


class EvaluatorAgent:
    """Evaluates support agent performance on completed training sessions."""

    def evaluate_session(self, messages: list[dict], persona_name: str,
                         category: str, difficulty: str,
                         issue_description: str, company_context: str) -> dict:
        """
        Run a full evaluation on a completed training session.

        Returns a structured evaluation with scores and feedback.
        """
        llm = ChatOllama(
            model=LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,  # Low temperature for consistent scoring
        )

        transcript = _format_transcript(messages)

        prompt = EVALUATION_PROMPT.format(
            persona_name=persona_name,
            category=category,
            difficulty=difficulty,
            issue_description=issue_description,
            company_context=company_context,
            transcript=transcript,
        )

        llm_messages = [
            {"role": "system", "content": "You are a customer support quality evaluator. "
                                           "Respond ONLY in valid JSON format."},
            {"role": "user", "content": prompt},
        ]

        response = llm.invoke(llm_messages)

        try:
            result_text = response.content.strip()

            # Handle markdown code block wrapping
            if "```" in result_text:
                parts = result_text.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        result_text = part
                        break

            result = json.loads(result_text)

            # Validate and clamp scores
            for key in ["empathy_score", "accuracy_score", "resolution_score",
                        "communication_score", "overall_score"]:
                score = result.get(key, 50)
                result[key] = max(0, min(100, float(score)))

            # Ensure overall_score is a weighted average if not provided properly
            if result.get("overall_score", 0) == 0:
                result["overall_score"] = round(
                    (result["empathy_score"] * 0.25 +
                     result["accuracy_score"] * 0.30 +
                     result["resolution_score"] * 0.30 +
                     result["communication_score"] * 0.15), 1
                )

            logger.info(f"Evaluation complete — Overall: {result['overall_score']}, "
                         f"Empathy: {result['empathy_score']}, "
                         f"Accuracy: {result['accuracy_score']}, "
                         f"Resolution: {result['resolution_score']}, "
                         f"Communication: {result['communication_score']}")

            return {
                "overall_score": result["overall_score"],
                "empathy_score": result["empathy_score"],
                "accuracy_score": result["accuracy_score"],
                "resolution_score": result["resolution_score"],
                "communication_score": result["communication_score"],
                "strengths": result.get("strengths", []),
                "improvements": result.get("improvements", []),
                "ideal_responses": result.get("ideal_responses", []),
                "summary": result.get("summary", "Evaluation complete."),
            }

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse evaluation response: {e}")
            logger.debug(f"Raw response: {response.content}")

            # Return default scores on parse failure
            return {
                "overall_score": 50.0,
                "empathy_score": 50.0,
                "accuracy_score": 50.0,
                "resolution_score": 50.0,
                "communication_score": 50.0,
                "strengths": [{"point": "Evaluation parsing failed — please retry", "quote": ""}],
                "improvements": [{"point": "Evaluation parsing failed — please retry", "quote": "", "suggestion": ""}],
                "ideal_responses": [],
                "summary": "Evaluation could not be fully parsed. Please retry.",
            }


# Singleton instance
evaluator_agent = EvaluatorAgent()
