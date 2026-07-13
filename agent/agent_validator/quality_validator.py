from typing import Dict

from .text_utils import TextUtils


class QualityValidator:

    def validate(self, response: str) -> Dict:

        score = 100
        issues = []
        suggestions = []

        if not response.strip():
            return {
                "score": 0,
                "issues": ["Empty response"],
                "suggestions": ["Generate a complete response"]
            }

        words = TextUtils.extract_words(response)
        sentences = TextUtils.extract_sentences(response)

        # Avoid fixed word lists.
        # Professional tone is evaluated semantically by the AI.

        if len(words) > 250:
            score -= 10
            issues.append("Response may be unnecessarily long")
            suggestions.append(
                "Make the response more concise while keeping useful information"
            )

        if len(sentences) < 2 and len(words) > 15:
            score -= 10
            issues.append("Low readability")
            suggestions.append(
                "Split the response into clearer sentences"
            )

        return {
            "score": max(0, min(score, 100)),
            "issues": issues,
            "suggestions": suggestions
        }
