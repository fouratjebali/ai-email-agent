from datetime import datetime
from typing import Dict, List
import json
import os
import re
import uuid

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import settings


class ResponseValidatorAgent:
    """
    Agent 2 V3:
    Advanced Hybrid Email Response Validator

    Features:
    - Rule-based validation
    - AI semantic validation
    - Security validation
    - Quality validation
    - Hybrid scoring
    - Critical semantic checks
    - Decision engine
    - Explainability
    - Human feedback
    - Validation history
    """

    def __init__(self, confidence_threshold: int = 85):

        self.name = "Response Validator Agent V3"
        self.confidence_threshold = confidence_threshold

        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0,
            num_predict=600,
            client_kwargs={
                "timeout": settings.OLLAMA_TIMEOUT_SECONDS
            }
        )

        self.history_file = "data/validation_history.json"
        self.feedback_file = "data/feedback.json"

    # ======================================================
    # TEXT UTILITIES
    # ======================================================

    def _extract_words(self, text: str) -> List[str]:
        return re.findall(
            r"\b\w+\b",
            text.lower(),
            flags=re.UNICODE
        )

    def _extract_sentences(self, text: str) -> List[str]:
        return [
            sentence.strip()
            for sentence in re.split(r"[.!?]+", text)
            if sentence.strip()
        ]

    # ======================================================
    # SECURITY VALIDATION
    # ======================================================

    def _security_validation(self, response: str) -> Dict:

        risks = []

        # Only detect high-confidence sensitive information.
        security_patterns = {
            "password": r"password\s*[:=]\s*\S+",
            "api_key": r"api[_\s-]?key\s*[:=]\s*\S+",
            "secret": r"secret\s*[:=]\s*\S+",
            "access_token": r"access[_\s-]?token\s*[:=]\s*\S+",
            "bearer_token": r"bearer\s+[A-Za-z0-9\-._~+/]+=*",
            "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        }

        for risk_name, pattern in security_patterns.items():
            if re.search(pattern, response, flags=re.IGNORECASE):
                risks.append(risk_name)

        if risks:
            return {
                "score": 0,
                "safe": False,
                "risks": risks,
                "message": "High-confidence sensitive information detected"
            }

        return {
            "score": 100,
            "safe": True,
            "risks": [],
            "message": "No critical security issue detected"
        }

    # ======================================================
    # RULE VALIDATION
    # ======================================================

    def _validate_rules(
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

        words = self._extract_words(generated_response)
        sentences = self._extract_sentences(generated_response)

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

        # Generic repetition detection.
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

    # ======================================================
    # QUALITY VALIDATION
    # ======================================================

    def _quality_validation(self, response: str) -> Dict:

        score = 100
        issues = []
        suggestions = []

        if not response.strip():
            return {
                "score": 0,
                "issues": ["Empty response"],
                "suggestions": ["Generate a complete response"]
            }

        words = self._extract_words(response)
        sentences = self._extract_sentences(response)

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

    # ======================================================
    # AI SEMANTIC VALIDATION
    # ======================================================

    def _validate_with_ai(
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
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
            )

            content = str(result.content).strip()

            # Remove accidental Markdown fences.
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
                "complete": bool(data.get("complete", False)),
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

    # ======================================================
    # HYBRID SCORE
    # ======================================================

    def _calculate_final_score(
        self,
        rule_score: int,
        ai_score: int,
        security_score: int,
        quality_score: int
    ) -> int:

        score = (
            rule_score * 0.30
            + ai_score * 0.40
            + security_score * 0.20
            + quality_score * 0.10
        )

        return round(score)

    # ======================================================
    # DECISION ENGINE
    # ======================================================

    def _decision_engine(
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

        if (
            score >= self.confidence_threshold
            and semantic_pass
        ):
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

    # ======================================================
    # RISK LEVEL
    # ======================================================

    def _risk_level(
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

    # ======================================================
    # EXPLAINABILITY
    # ======================================================

    def _explainability(
        self,
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

    # ======================================================
    # SAVE VALIDATION HISTORY
    # ======================================================

    def _save_history(self, result: Dict) -> None:

        os.makedirs(
            os.path.dirname(self.history_file),
            exist_ok=True
        )

        with open(
            self.history_file,
            "a",
            encoding="utf-8"
        ) as file:
            file.write(
                json.dumps(
                    result,
                    ensure_ascii=False
                )
                + "\n"
            )

    # ======================================================
    # HUMAN FEEDBACK
    # ======================================================

    def save_feedback(
        self,
        validation_id: str,
        email_id: str,
        agent_decision: str,
        human_decision: str,
        comment: str = ""
    ) -> Dict:

        os.makedirs(
            os.path.dirname(self.feedback_file),
            exist_ok=True
        )

        feedback = {
            "id": str(uuid.uuid4()),
            "validation_id": validation_id,
            "email_id": email_id,
            "agent_decision": agent_decision,
            "human_decision": human_decision,
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        }

        with open(
            self.feedback_file,
            "a",
            encoding="utf-8"
        ) as file:
            file.write(
                json.dumps(
                    feedback,
                    ensure_ascii=False
                )
                + "\n"
            )

        return feedback

    # ======================================================
    # MAIN VALIDATION
    # ======================================================

    def validate(
        self,
        original_email: str,
        generated_response: str,
        email_id: str = ""
    ) -> Dict:

        validation_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        rule = self._validate_rules(
            original_email,
            generated_response
        )

        security = self._security_validation(
            generated_response
        )

        quality = self._quality_validation(
            generated_response
        )

        # Missing input protection.
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

            self._save_history(result)
            return result

        ai = self._validate_with_ai(
            original_email,
            generated_response
        )

        # Fail-safe if Ollama is unavailable.
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

            self._save_history(result)
            return result

        final_score = self._calculate_final_score(
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

        decision = self._decision_engine(
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
            "risk_level": self._risk_level(
                final_score,
                decision["decision"]
            ),
            "approved": (
                decision["decision"] == "APPROVED"
            ),
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
            "explainability": self._explainability(
                scores=scores,
                issues=issues,
                suggestions=suggestions,
                decision=decision["decision"]
            )
        }

        self._save_history(result)

        return result
