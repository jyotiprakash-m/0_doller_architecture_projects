"""
Feedback Agent — Generates personalized, actionable coaching feedback.
"""
import logging
import json
from langchain_ollama import ChatOllama
from config import OLLAMA_BASE_URL, LLM_MODEL

logger = logging.getLogger(__name__)

FEEDBACK_PROMPT = """You are a customer support training coach. Based on the evaluation and transcript, provide coaching feedback.

SCORES: Overall={overall_score}, Empathy={empathy_score}, Accuracy={accuracy_score}, Resolution={resolution_score}, Communication={communication_score}
SCENARIO: {persona_name} | {category} | {difficulty}

TRANSCRIPT:
{transcript}

COMPANY KNOWLEDGE:
{company_context}

Respond ONLY in JSON:
{{"overall_assessment": "summary", "did_well": [{{"point": "desc", "quote": "quote"}}], "improve": [{{"point": "desc", "agent_said": "quote", "better_alternative": "suggestion"}}], "key_takeaways": ["tip1", "tip2", "tip3"], "difficulty_recommendation": "increase|maintain|decrease", "encouragement": "message"}}"""


def _format_transcript(messages):
    lines = []
    for msg in messages:
        role = "CUSTOMER" if msg["role"] == "customer" else "AGENT"
        lines.append(f"{role}: {msg['content']}")
    return "\n\n".join(lines)


class FeedbackAgent:
    def generate_feedback(self, evaluation, messages, persona_name, category, difficulty, company_context):
        llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.3)
        transcript = _format_transcript(messages)
        prompt = FEEDBACK_PROMPT.format(
            overall_score=evaluation.get("overall_score", 50),
            empathy_score=evaluation.get("empathy_score", 50),
            accuracy_score=evaluation.get("accuracy_score", 50),
            resolution_score=evaluation.get("resolution_score", 50),
            communication_score=evaluation.get("communication_score", 50),
            persona_name=persona_name, category=category, difficulty=difficulty,
            transcript=transcript, company_context=company_context,
        )
        response = llm.invoke([
            {"role": "system", "content": "You are a supportive training coach. Respond ONLY in valid JSON."},
            {"role": "user", "content": prompt},
        ])
        try:
            result_text = response.content.strip()
            if "```" in result_text:
                parts = result_text.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"): part = part[4:].strip()
                    if part.startswith("{"): result_text = part; break
            result = json.loads(result_text)
            return {
                "overall_assessment": result.get("overall_assessment", "Good effort!"),
                "did_well": result.get("did_well", []),
                "improve": result.get("improve", []),
                "key_takeaways": result.get("key_takeaways", []),
                "difficulty_recommendation": result.get("difficulty_recommendation", "maintain"),
                "encouragement": result.get("encouragement", "Keep practicing!"),
            }
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse feedback: {e}")
            return {
                "overall_assessment": "Good effort! Review the transcript to identify improvement areas.",
                "did_well": [{"point": "Completed the session", "quote": ""}],
                "improve": [{"point": "Please retry feedback generation", "agent_said": "", "better_alternative": ""}],
                "key_takeaways": ["Acknowledge feelings first", "Reference company policies", "End with clear next steps"],
                "difficulty_recommendation": "maintain",
                "encouragement": "Every session makes you better!",
            }

feedback_agent = FeedbackAgent()
