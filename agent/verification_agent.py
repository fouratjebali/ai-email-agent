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
        if not generated_response or not generated_response.strip():

            issues.append(
                "Generated response is empty"
            )

            suggestions.append(
                "Generate a valid email response"
            )

            score -= 40


        else:

            response = generated_response.strip()


            # 2. Check response length
            word_count = len(response.split())

            if word_count < 15:

                issues.append(
                    "Response lacks sufficient details"
                )

                suggestions.append(
                    "Provide a more complete explanation"
                )

                score -= 10



            # 3. Check response structure

            lines = response.split("\n")

            if len(lines) < 2:

                issues.append(
                    "Response structure is too simple"
                )

                suggestions.append(
                    "Organize the response clearly"
                )

                score -= 5



            # 4. Check sentence completeness

            sentences = [
                sentence.strip()
                for sentence in response.split(".")
                if sentence.strip()
            ]


            if len(sentences) == 0:

                issues.append(
                    "Response does not contain complete sentences"
                )

                suggestions.append(
                    "Use clear and complete sentences"
                )

                score -= 10



            # 5. Check readability

            if len(sentences) > 0:

                average_sentence_length = (
                    word_count / len(sentences)
                )


                if average_sentence_length < 3:

                    issues.append(
                        "Response may be unclear or fragmented"
                    )

                    suggestions.append(
                        "Write more natural sentences"
                    )

                    score -= 5



            # 6. Context validation

            original_words = set(
                original_email.lower().split()
            )

            response_words = set(
                response.lower().split()
            )


            if original_words and response_words:

                common_words = (
                    original_words.intersection(response_words)
                )


                if len(common_words) < 2:

                    issues.append(
                        "Response may not match the original email context"
                    )

                    suggestions.append(
                        "Verify that the response addresses the user's request"
                    )

                    score -= 15



            # 7. Security validation

            suspicious_patterns = [
                "password",
                "secret",
                "api key",
                "token"
            ]


            for pattern in suspicious_patterns:

                if pattern in response.lower():

                    issues.append(
                        "Response may contain sensitive information"
                    )

                    suggestions.append(
                        "Review sensitive data before sending"
                    )

                    score -= 20

                    break



            # 8. Repetition check

            words = response.lower().split()

            if len(words) > 0:

                unique_words = set(words)

                repetition_ratio = (
                    len(unique_words) / len(words)
                )


                if repetition_ratio < 0.5:

                    issues.append(
                        "Response contains excessive repetition"
                    )

                    suggestions.append(
                        "Improve response diversity and clarity"
                    )

                    score -= 5



            # 9. Check if response answers a request

            if "?" in original_email:

                if len(response.split()) < 20:

                    issues.append(
                        "Response may not fully answer the request"
                    )

                    suggestions.append(
                        "Provide a more complete answer"
                    )

                    score -= 10



        # 10. Check original email availability

        if not original_email or not original_email.strip():

            issues.append(
                "Original email content is missing"
            )

            suggestions.append(
                "Provide the original email for validation"
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
