"""
Scenario Generator — Auto-generates training scenarios from knowledge base content.
Uses RAG context to create realistic, company-specific customer personas and issues.
"""
import logging
import json
from langchain_ollama import ChatOllama
from config import OLLAMA_BASE_URL, LLM_MODEL, SCENARIO_CATEGORIES, DIFFICULTY_LEVELS

logger = logging.getLogger(__name__)

SCENARIO_PROMPT = """You are a training scenario designer for customer support. Based on the company knowledge below, generate {count} realistic training scenarios.

COMPANY KNOWLEDGE:
{company_context}

REQUIREMENTS:
- Each scenario should have a unique customer persona with a name, backstory, and specific issue
- Cover different categories: {categories}
- Include a mix of difficulties: {difficulties}
- Issues should reference real products/services/policies from the company knowledge
- Make personas feel like real people with distinct personalities

Respond ONLY in this JSON format:
{{"scenarios": [
  {{
    "persona_name": "FirstName LastName",
    "persona_description": "Brief backstory and personality (2-3 sentences)",
    "issue_description": "The specific problem this customer is facing",
    "category": "one of: {categories}",
    "difficulty": "easy|medium|hard",
    "expected_resolution": "What a good agent should do to resolve this",
    "initial_emotional_state": "neutral|frustrated|angry"
  }}
]}}"""


class ScenarioGenerator:
    def generate_scenarios(self, company_context: str, count: int = 3) -> list[dict]:
        llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.8)
        categories = ", ".join(SCENARIO_CATEGORIES)
        difficulties = ", ".join(DIFFICULTY_LEVELS)
        prompt = SCENARIO_PROMPT.format(
            count=count, company_context=company_context,
            categories=categories, difficulties=difficulties,
        )
        response = llm.invoke([
            {"role": "system", "content": "You are a creative scenario designer. Respond ONLY in valid JSON."},
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
            scenarios = result.get("scenarios", [])[:count]
            # Validate each scenario
            validated = []
            for s in scenarios:
                validated.append({
                    "persona_name": s.get("persona_name", "Unknown Customer"),
                    "persona_description": s.get("persona_description", "A customer needing help."),
                    "issue_description": s.get("issue_description", "General inquiry"),
                    "category": s.get("category", "general_inquiry") if s.get("category") in SCENARIO_CATEGORIES else "general_inquiry",
                    "difficulty": s.get("difficulty", "medium") if s.get("difficulty") in DIFFICULTY_LEVELS else "medium",
                    "expected_resolution": s.get("expected_resolution", "Resolve the customer's issue"),
                    "initial_emotional_state": s.get("initial_emotional_state", "neutral"),
                })
            logger.info(f"Generated {len(validated)} scenarios from KB context")
            return validated
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse scenarios: {e}")
            return self._fallback_scenarios()

    def _fallback_scenarios(self) -> list[dict]:
        return [
            {
                "persona_name": "Sarah Mitchell",
                "persona_description": "A busy professional who values efficiency. She's been a customer for 2 years.",
                "issue_description": "Having trouble accessing her account after a recent password change.",
                "category": "account_issue",
                "difficulty": "easy",
                "expected_resolution": "Guide through password reset process and verify account access.",
                "initial_emotional_state": "neutral",
            },
            {
                "persona_name": "James Rodriguez",
                "persona_description": "A tech-savvy user who expects quick, accurate answers. Gets frustrated with scripted responses.",
                "issue_description": "Charged twice for the same subscription renewal this month.",
                "category": "billing",
                "difficulty": "medium",
                "expected_resolution": "Acknowledge the error, initiate a refund, and verify billing settings.",
                "initial_emotional_state": "frustrated",
            },
            {
                "persona_name": "Karen Thompson",
                "persona_description": "A long-time customer who feels undervalued. Has had multiple issues in the past month.",
                "issue_description": "Wants to cancel subscription due to repeated service outages and poor support experiences.",
                "category": "cancellation",
                "difficulty": "hard",
                "expected_resolution": "Empathize, acknowledge past issues, offer retention incentive, address root concerns.",
                "initial_emotional_state": "angry",
            },
        ]

scenario_generator = ScenarioGenerator()
