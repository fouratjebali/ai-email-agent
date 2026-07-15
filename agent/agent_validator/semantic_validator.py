import json
import re
from typing import Dict

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

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


    def calculate_score(self, data):

        score = 0

        if data.get("relevant"):
            score += 25

        if data.get("answers_request"):
            score += 25

        if data.get("professional"):
            score += 25

        if data.get("complete"):
            score += 25

        if data.get("contradiction"):
            score -= 20

        if data.get("hallucination"):
            score -= 20

        return max(0, min(score, 100))


    def validate(
        self,
        original_email: str,
        generated_response: str
    ) -> Dict:

        try:

            prompt = f"""
You are a strict semantic validator for an email response.

Original email/request:
{original_email}

Generated response:
{generated_response}

Analyze if the response truly satisfies the request.

Rules:

1. If the response refuses to answer:
- answers_request=false
- complete=false

2. If the response does not provide the requested information:
- relevant=false
- answers_request=false

3. Check:
- relevant
- answers_request
- professional
- complete
- contradiction
- hallucination

Return ONLY JSON:

{{
"relevant":true,
"answers_request":true,
"professional":true,
"complete":true,
"contradiction":false,
"hallucination":false,
"issues":[],
"suggestions":[]
}}
"""


            result = self.llm.invoke(
                [
                    SystemMessage(
                        content="You are a semantic validator."
                    ),
                    HumanMessage(
                        content=prompt
                    )
                ]
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

                "score": self.calculate_score(data),

                "relevant": bool(
                    data.get("relevant", False)
                ),

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
