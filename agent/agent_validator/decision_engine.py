from typing import Dict


class DecisionEngine:

    def __init__(self, confidence_threshold: int = 85):
        self.confidence_threshold = confidence_threshold

    def make_decision(
        self,
        score: int,
        security_safe: bool,
        semantic_pass: bool,
        contradiction: bool,
        hallucination: bool
    ) -> Dict:

        # Security problems always block the response.
        if not security_safe:
            return {
                "decision": "BLOCKED",
                "action": "BLOCK_RESPONSE"
            }

        # Critical semantic errors must not be compensated
        # by a high global score.
        if contradiction or hallucination:
            return {
                "decision": "REJECTED",
                "action": "REGENERATE_RESPONSE"
            }

        if score >= self.confidence_threshold and semantic_pass:
            return {
                "decision": "APPROVED",
                "action": "SEND_EMAIL"
            }

        if score >= 60:
            return {
                "decision": "NEEDS_REVIEW",
                "action": "HUMAN_REVIEW"
            }

        return {
            "decision": "REJECTED",
            "action": "REGENERATE_RESPONSE"
        }

    def risk_level(
        self,
        score: int,
        decision: str
    ) -> str:

        # Decision takes priority over the numerical score.
        if decision == "BLOCKED":
            return "CRITICAL"

        if decision == "REJECTED":
            return "HIGH"

        if decision == "NEEDS_REVIEW":
            return "MEDIUM"

        if score >= self.confidence_threshold:
            return "LOW"

        return "MEDIUM"
