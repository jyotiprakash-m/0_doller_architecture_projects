import logging
import json
from langchain_ollama import ChatOllama
from config import OLLAMA_BASE_URL, LLM_MODEL

logger = logging.getLogger(__name__)

SUGGESTION_PROMPT = """You are an AI Co-pilot for a customer support executive. 
The executive needs to reply to the customer's last message.

COMPANY KNOWLEDGE (Use this to provide factual, correct answers):
{company_context}

CUSTOMER PERSONA: {persona_name}
ISSUE: {issue_description}
CONVERSATION SO FAR:
{chat_history}

Generate exactly 3 different suggested replies for the executive to send to the customer. 
Ensure the replies are based on the COMPANY KNOWLEDGE provided. If the knowledge doesn't contain the exact answer, provide a professional response indicating you will look into it.

Provide 3 distinct styles:
1. Empathetic: Focus on apologizing and making the customer feel heard, while providing the solution.
2. Direct: Get straight to the point and provide the solution efficiently.
3. Detailed: Provide a comprehensive explanation of the solution or policy.

Respond ONLY in this JSON format:
{{
  "suggestions": [
    {{"style": "Empathetic", "message": "..."}},
    {{"style": "Direct", "message": "..."}},
    {{"style": "Detailed", "message": "..."}}
  ]
}}
"""

class SuggestionAgent:
    def generate_suggestions(self, persona_name: str, issue_description: str,
                             messages: list[dict], company_context: str) -> list[dict]:
        """Generate 3 suggested responses for the trainee."""
        llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.7)

        # Format chat history
        chat_history = ""
        for m in messages[-4:]: # Only need the last few messages for context
            role = "Customer" if m["role"] == "customer" else "Agent"
            chat_history += f"{role}: {m['content']}\n"

        prompt = SUGGESTION_PROMPT.format(
            company_context=company_context,
            persona_name=persona_name,
            issue_description=issue_description,
            chat_history=chat_history.strip()
        )

        response = llm.invoke([
            {"role": "system", "content": "You are a helpful co-pilot. Respond ONLY in valid JSON."},
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
            suggestions = result.get("suggestions", [])[:3]
            
            # Ensure we have exactly 3 and format is correct
            formatted = []
            for s in suggestions:
                message = s.get("message", "I am looking into this right now.")
                if isinstance(message, dict):
                    # Handle hallucinated objects like {"text": "...", "body": "..."}
                    message = message.get("text") or message.get("body") or message.get("content") or message.get("message") or str(message)
                elif not isinstance(message, str):
                    message = str(message)

                formatted.append({
                    "style": str(s.get("style", "Alternative")),
                    "message": message
                })
            return formatted
            
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            return [
                {"style": "Empathetic", "message": "I completely understand how frustrating this is. Let me look up the policy and sort this out for you right away."},
                {"style": "Direct", "message": "Let me check our records and provide you with a quick resolution to this issue."},
                {"style": "Detailed", "message": "Thank you for reaching out. I'm going to review the details of your issue alongside our current policies to give you a complete answer."}
            ]

suggestion_agent = SuggestionAgent()
