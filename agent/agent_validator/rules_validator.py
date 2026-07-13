from typing import Dict

from .text_utils import TextUtils


class RulesValidator:

    def validate(
        self,
        original_email: str,
        generated_response: str
    ) -> Dict:

        score = 100
        issues = []
        suggestions = []

        if not original_email.strip():
            score -= 40
            issues.append("Original email missing")
            suggestions.append("Provide the original email")

        if not generated_response.strip():
            score -= 60
            issues.append("Generated response empty")
            suggestions.append("Generate a response")

            return {
                "score": max(score, 0),
                "issues": issues,
                "suggestions": suggestions
            }

        words = TextUtils.extract_words(generated_response)
        sentences = TextUtils.extract_sentences(generated_response)

        word_count = len(words)

        if word_count < 5:
            score -= 25
            issues.append("Response too short")
            suggestions.append(
                "Add enough information to answer the request"
            )

        elif word_count < 15:
            score -= 10
            issues.append("Response may lack details")
            suggestions.append(
                "Check whether all important information is included"
            )

        if not sentences:
            score -= 10
            issues.append("Invalid sentence structure")
            suggestions.append(
                "Improve the structure and readability of the response"
            )

        if word_count > 20:
            diversity = len(set(words)) / word_count

            if diversity < 0.35:
                score -= 10
                issues.append("Excessive repetition")
                suggestions.append(
                    "Reduce repeated words and sentences"
                )

        return {
            "score": max(0, min(score, 100)),
            "issues": issues,
            "suggestions": suggestions
        }
