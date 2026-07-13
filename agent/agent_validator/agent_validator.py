from datetime import datetime
from typing import Dict
import uuid

from .rules_validator import RulesValidator
from .security_validator import SecurityValidator
from .quality_validator import QualityValidator
from .semantic_validator import SemanticValidator
from .score_calculator import ScoreCalculator
from .decision_engine import DecisionEngine
from .explainability import Explainability
from .history_manager import HistoryManager
from .feedback_manager import FeedbackManager


class ResponseValidatorAgent:
    """
    Agent 2 V3:
    Advanced Hybrid Email Response Validator
    """

    def __init__(self, confidence_threshold: int = 85):

        self.name = "Response Validator Agent V3"
        self.confidence_threshold = confidence_threshold

        self.rules_validator = RulesValidator()
        self.security_validator = SecurityValidator()
        self.quality_validator = QualityValidator()
        self.semantic_validator = SemanticValidator()

        self.decision_engine = DecisionEngine(
            confidence_threshold
        )

        self.history = HistoryManager()
        self.feedback = FeedbackManager()
    def save_feedback(
        self,
        validation_id: str,
        email_id: str,
        agent_decision: str,
        human_decision: str,
        comment: str = ""
    ):
        return self.feedback.save(
            validation_id,
            email_id,
            agent_decision,
            human_decision,
            comment
        )
    def validate(
        self,
        original_email: str,
        generated_response: str,
        email_id: str = ""
    ) -> Dict:

        validation_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        rule = self.rules_validator.validate(
            original_email,
            generated_response
        )

        security = self.security_validator.validate(
            generated_response
        )

        quality = self.quality_validator.validate(
            generated_response
        )

        # Missing input protection
        if (
            not original_email.strip()
            or not generated_response.strip()
        ):

            result = {
                "validation_id": validation_id,
                "email_id": email_id,
                "agent": self.name,
                "timestamp": timestamp,
                "confidence_score": 0,
                "risk_level": "CRITICAL",
                "approved": False,
                "decision": "REJECTED",
                "action": "REGENERATE_RESPONSE",
                "scores": {
                    "rules": rule["score"],
                    "ai": 0,
                    "security": security["score"],
                    "quality": quality["score"]
                },
                "issues": ["Missing input data"],
                "suggestions": [
                    "Provide both the original email and generated response"
                ]
            }

            self.history.save(result)
            return result

        ai = self.semantic_validator.validate(
            original_email,
            generated_response
        )

        # Fail-safe if AI validation is unavailable
        if not ai["success"]:

            result = {
                "validation_id": validation_id,
                "email_id": email_id,
                "agent": self.name,
                "timestamp": timestamp,
                "confidence_score": 0,
                "risk_level": "HIGH",
                "approved": False,
                "decision": "NEEDS_REVIEW",
                "action": "HUMAN_REVIEW",
                "scores": {
                    "rules": rule["score"],
                    "ai": 0,
                    "security": security["score"],
                    "quality": quality["score"]
                },
                "issues": ai["issues"],
                "suggestions": ai["suggestions"]
            }

            self.history.save(result)
            return result

        final_score = ScoreCalculator.calculate(
            rule["score"],
            ai["score"],
            security["score"],
            quality["score"]
        )

        issues = list(
            dict.fromkeys(
                rule["issues"]
                + ai["issues"]
                + quality["issues"]
                + security["risks"]
            )
        )

        suggestions = list(
            dict.fromkeys(
                rule["suggestions"]
                + ai["suggestions"]
                + quality["suggestions"]
            )
        )

        semantic_pass = all(
            [
                ai["relevant"],
                ai["answers_request"],
                ai["professional"],
                ai["complete"],
                not ai["contradiction"],
                not ai["hallucination"]
            ]
        )

        decision = self.decision_engine.make_decision(
            score=final_score,
            security_safe=security["safe"],
            semantic_pass=semantic_pass,
            contradiction=ai["contradiction"],
            hallucination=ai["hallucination"]
        )

        scores = {
            "rules": rule["score"],
            "ai": ai["score"],
            "security": security["score"],
            "quality": quality["score"]
        }

        result = {
            "validation_id": validation_id,
            "email_id": email_id,
            "agent": self.name,
            "timestamp": timestamp,
            "confidence_score": final_score,
            "risk_level": self.decision_engine.risk_level(
                final_score,
                decision["decision"]
            ),
            "approved": decision["decision"] == "APPROVED",
            "decision": decision["decision"],
            "action": decision["action"],
            "scores": scores,
            "issues": issues,
            "suggestions": suggestions,
            "semantic_analysis": {
                "relevant": ai["relevant"],
                "answers_request": ai["answers_request"],
                "professional": ai["professional"],
                "complete": ai["complete"],
                "contradiction": ai["contradiction"],
                "hallucination": ai["hallucination"]
            },
            "explainability": Explainability.generate(
                scores=scores,
                issues=issues,
                suggestions=suggestions,
                decision=decision["decision"]
            )
        }

        self.history.save(result)

        return result
