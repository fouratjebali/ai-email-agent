from datetime import datetime
from typing import Dict, List


class ResponseValidatorAgent:
    """
    Agent 2:
    Validates AI-generated email responses before sending them.
    """

    def __init__(self, confidence_threshold: int = 80):
        self.name = "Response Validator Agent"
        self.confidence_threshold = confidence_threshold


    def validate(
        self,
        original_email: str,
        generated_response: str
    ) -> Dict:

        issues: List[str] = []
        suggestions: List[str] = []

        score = 100


        # 1. Check if response exists
        if not generated_response:
            issues.append("Generated response is empty")
            score -= 40


        # 2. Check response length
        if len(generated_response) < 50:
            issues.append("Response is too short")
            suggestions.append(
                "Generate a more detailed answer"
            )
            score -= 15


        # 3. Check professional tone
        professional_terms = [
            "hello",
            "dear",
            "thank you",
            "regards",
            "best regards",
            "cordially"
        ]

        response_lower = generated_response.lower()

        if not any(
            term in response_lower
            for term in professional_terms
        ):
            issues.append(
                "Professional greeting or closing missing"
            )
            suggestions.append(
                "Add a professional greeting and closing"
            )
            score -= 10


        # 4. Check if original email exists
        if not original_email:
            issues.append(
                "Original email content missing"
            )
            score -= 20


        # Final decision
        approved = score >= self.confidence_threshold


        return {
            "agent": self.name,
            "timestamp": datetime.now().isoformat(),
            "approved": approved,
            "confidence_score": max(score, 0),
            "issues": issues,
            "suggestions": suggestions,
            "action":
                "SEND_EMAIL"
                if approved
                else "REVIEW_REQUIRED"
        }
