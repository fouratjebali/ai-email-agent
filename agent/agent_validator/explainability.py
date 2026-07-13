from typing import Dict, List


class Explainability:

    @staticmethod
    def generate(
        scores: Dict,
        issues: List[str],
        suggestions: List[str],
        decision: str
    ) -> Dict:

        if decision == "APPROVED":
            reason = "All required validation checks passed"

        elif decision == "BLOCKED":
            reason = "The response contains a critical security risk"

        elif decision == "REJECTED":
            reason = (
                "Critical validation problems require response regeneration"
            )

        else:
            reason = (
                "The response requires human verification before sending"
            )

        return {
            "scores": scores,
            "detected_issues": issues,
            "suggestions": suggestions,
            "decision_reason": reason,
            "final_decision": decision
        }
