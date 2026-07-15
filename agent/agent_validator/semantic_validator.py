import json
import re
from typing import Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from config.settings import settings


class SemanticValidator:

    def __init__(self):

        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0,
            num_predict=128,
            client_kwargs={
                "timeout": settings.OLLAMA_TIMEOUT_SECONDS
            }
        )

    def validate(
        self,
        original_email: str,
        generated_response: str
    ) -> Dict:

        system_prompt = """
You are an expert email response validation AI.

Your task is to compare a generated email response with the
original email.

Evaluate:

1. Relevance:
Does the response address the same topic and customer intent?

2. Request coverage:
Does the response answer the actual request?

3. Professional tone:
Is the tone appropriate for a professional email?

4. Completeness:
Does the response contain enough information?

5. Contradiction:
Does the response contradict the original email?

6. Hallucination:
Does the response invent facts, promises, dates, prices,
decisions, actions, or information not supported by the
original email?

Return ONLY valid JSON.

Required format:

{
    "score": 0,
    "relevant": true,
    "answers_request": true,
    "professional": true,
    "complete": true,
    "contradiction": false,
    "hallucination": false,
    "issues": [],
    "suggestions": []
}

The score must be an integer between 0 and 100.
Do not use markdown.
Do not add text before or after the JSON.
"""

        user_prompt = f"""
ORIGINAL EMAIL:

{original_email}

GENERATED RESPONSE:

{generated_response}
"""

        try:

            result = self.llm.invoke(
    """
Return ONLY this JSON exactly:

{
    "score": 100,
    "relevant": true,
    "answers_request": true,
    "professional": true,
    "complete": true,
    "contradiction": false,
    "hallucination": false,
    "issues": [],
    "suggestions": []
}
"""
)

            content = str(result.content).strip()

            content = re.sub(
                r"```(?:json)?|```",
                "",
                content,
                flags=re.IGNORECASE
            ).strip()

            data = json.loads(content)

            return {
                "success": True,
                "score": max(
                    0,
                    min(int(data.get("score", 0)), 100)
                ),
                "relevant": bool(data.get("relevant", False)),
                "answers_request": bool(
                    data.get("answers_request", False)
                ),
                "professional": bool(
                    data.get("professional", False)
                ),
                "complete": bool(
                    data.get("complete", False)
                ),
                "contradiction": bool(
                    data.get("contradiction", False)
                ),
                "hallucination": bool(
                    data.get("hallucination", False)
                ),
                "issues": data.get("issues", []),
                "suggestions": data.get("suggestions", [])
            }

        except Exception as error:

            print("Semantic Validator Error:", error)

            return {
                "success": False,
                "score": 0,
                "relevant": False,
                "answers_request": False,
                "professional": False,
                "complete": False,
                "contradiction": False,
                "hallucination": False,
                "issues": [
                    "AI validation unavailable"
                ],
                "suggestions": [
                    "Human review required"
                ],
                "error": str(error)
            }

