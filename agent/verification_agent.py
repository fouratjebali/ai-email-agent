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
    Agent 2 V2:
    Advanced Hybrid Email Response Validator

    Features:
    - Rule validation
    - AI semantic validation
    - Security validation
    - Quality scoring
    - Hybrid scoring
    - Decision engine
    - Explainability
    - Human feedback
    - Validation history
    """

    def __init__(
        self,
        confidence_threshold: int = 80
    ):

        self.name = "Response Validator Agent V2"

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


        self.history_file = (
            "data/validation_history.json"
        )

        self.feedback_file = (
            "data/feedback.json"
        )


    # ======================================================
    # TEXT UTILITIES
    # ======================================================


    def _extract_words(
        self,
        text:str
    ) -> List[str]:

        return re.findall(
            r"\b\w+\b",
            text.lower(),
            flags=re.UNICODE
        )



    def _extract_sentences(
        self,
        text:str
    ) -> List[str]:

        return [
            s.strip()
            for s in re.split(
                r"[.!?]+",
                text
            )
            if s.strip()
        ]



    # ======================================================
    # SECURITY VALIDATION
    # ======================================================


    def _security_validation(
        self,
        response:str
    ) -> Dict:


        risks = []


        security_patterns = {

            "password":
            r"password\s*[:=]\s*\S+",


            "api_key":
            r"api[_\s-]?key\s*[:=]\s*\S+",


            "secret":
            r"secret\s*[:=]\s*\S+",


            "token":
            r"(bearer\s+|access[_\s-]?token\s*[:=])\S+",


            "private_key":
            r"-----BEGIN PRIVATE KEY-----",


            "credit_card":
            r"\b\d{16}\b",


            "iban":
            r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{10,30}\b",


            "phone_number":
            r"\b\d{8,15}\b"
        }



        for name, pattern in security_patterns.items():

            if re.search(
                pattern,
                response,
                flags=re.IGNORECASE
            ):

                risks.append(name)



        if risks:

            return {

                "score":20,

                "safe":False,

                "risks":risks,

                "message":
                "Sensitive information detected"

            }



        return {

            "score":100,

            "safe":True,

            "risks":[],

            "message":
            "No security issue detected"

        }
    # ======================================================
    # RULE VALIDATION
    # ======================================================


    def _validate_rules(
        self,
        original_email:str,
        generated_response:str
    ) -> Dict:


        score = 100

        issues = []

        suggestions = []


        if not original_email.strip():

            score -= 40

            issues.append(
                "Original email missing"
            )

            suggestions.append(
                "Provide original customer email"
            )


        if not generated_response.strip():

            score -= 60

            issues.append(
                "Generated response empty"
            )

            suggestions.append(
                "Generate a response"
            )


            return {

                "score":max(score,0),

                "issues":issues,

                "suggestions":suggestions
            }



        words = self._extract_words(
            generated_response
        )


        sentences = self._extract_sentences(
            generated_response
        )


        word_count = len(words)



        # Response length

        if word_count < 5:

            score -= 25

            issues.append(
                "Response too short"
            )

            suggestions.append(
                "Add more information"
            )



        elif word_count < 15:

            score -= 10

            issues.append(
                "Response lacks details"
            )



        # Sentence structure

        if not sentences:

            score -= 10

            issues.append(
                "Invalid sentence structure"
            )


        # Repetition detection

        if word_count > 20:

            diversity = (
                len(set(words))
                /
                word_count
            )


            if diversity < 0.35:

                score -= 10

                issues.append(
                    "Excessive repetition"
                )



        return {

            "score":
            max(0,min(score,100)),

            "issues":
            issues,

            "suggestions":
            suggestions

        }




    # ======================================================
    # QUALITY VALIDATION
    # ======================================================


    def _quality_validation(
        self,
        response:str
    ) -> Dict:


        score = 100

        issues = []



        words = self._extract_words(
            response
        )



        sentences = self._extract_sentences(
            response
        )



        # Empty response

        if not response.strip():

            return {

                "score":0,

                "issues":[
                    "Empty response"
                ]

            }



        # Professional style

        informal_patterns = [

            r"\bok\b",

            r"\byeah\b",

            r"\bnope\b",

            r"\bthx\b"

        ]


        for pattern in informal_patterns:

            if re.search(
                pattern,
                response,
                flags=re.IGNORECASE
            ):

                score -= 10

                issues.append(
                    "Informal language detected"
                )



        # Very long response

        if len(words) > 250:

            score -= 10

            issues.append(
                "Response too long"
            )



        # Missing structure

        if len(sentences) < 2:

            score -= 10

            issues.append(
                "Low readability"
            )



        return {

            "score":
            max(score,0),

            "issues":
            issues

        }





    # ======================================================
    # AI SEMANTIC VALIDATION
    # ======================================================


    def _validate_with_ai(
        self,
        original_email:str,
        generated_response:str
    ) -> Dict:



        system_prompt = """

You are an expert email validation AI.

Analyze the response compared to the original email.

Evaluate:

- customer intent matching
- answer correctness
- completeness
- professional tone
- hallucinations
- unsupported claims
- contradictions

Return ONLY JSON.

Format:

{
 "score":0,
 "relevant":true,
 "answers_request":true,
 "professional":true,
 "complete":true,
 "contradiction":false,
 "hallucination":false,
 "issues":[],
 "suggestions":[]
}

Score 0-100.

No markdown.

"""



        user_prompt = f"""

CUSTOMER EMAIL:

{original_email}


GENERATED RESPONSE:

{generated_response}

"""



        try:


            result = self.llm.invoke(

                [

                    SystemMessage(
                        content=system_prompt
                    ),

                    HumanMessage(
                        content=user_prompt
                    )

                ]

            )



            content = str(
                result.content
            ).strip()



            content = re.sub(
                r"```json|```",
                "",
                content
            ).strip()



            data = json.loads(
                content
            )



            return {

                "success":True,

                "score":
                max(
                    0,
                    min(
                        int(data.get("score",0)),
                        100
                    )
                ),

                "relevant":
                bool(
                    data.get(
                        "relevant",
                        False
                    )
                ),

                "answers_request":
                bool(
                    data.get(
                        "answers_request",
                        False
                    )
                ),

                "professional":
                bool(
                    data.get(
                        "professional",
                        False
                    )
                ),

                "complete":
                bool(
                    data.get(
                        "complete",
                        False
                    )
                ),

                "contradiction":
                bool(
                    data.get(
                        "contradiction",
                        False
                    )
                ),

                "hallucination":
                bool(
                    data.get(
                        "hallucination",
                        False
                    )
                ),

                "issues":
                data.get(
                    "issues",
                    []
                ),

                "suggestions":
                data.get(
                    "suggestions",
                    []
                )

            }



        except Exception as e:


            return {

                "success":False,

                "score":0,

                "issues":[
                    "AI validation unavailable"
                ],

                "suggestions":[
                    "Human review required"
                ],

                "error":
                str(e)

            }
    # ======================================================
    # HYBRID SCORE
    # ======================================================


    def _calculate_final_score(
        self,
        rule_score:int,
        ai_score:int,
        security_score:int,
        quality_score:int
    ) -> int:


        score = (

            rule_score * 0.30

            +

            ai_score * 0.40

            +

            security_score * 0.20

            +

            quality_score * 0.10

        )


        return round(score)




    # ======================================================
    # DECISION ENGINE
    # ======================================================


    def _decision_engine(
        self,
        score:int,
        security_safe:bool,
        semantic_pass:bool
    ) -> Dict:


        if not security_safe:

            return {

                "decision":
                "BLOCKED",

                "action":
                "BLOCK_RESPONSE"

            }



        if (

            score >= 85

            and

            semantic_pass

        ):

            return {

                "decision":
                "APPROVED",

                "action":
                "SEND_EMAIL"

            }



        elif score >=60:

            return {

                "decision":
                "NEEDS_REVIEW",

                "action":
                "HUMAN_REVIEW"

            }



        else:

            return {

                "decision":
                "REJECTED",

                "action":
                "REGENERATE_RESPONSE"

            }





    # ======================================================
    # RISK LEVEL
    # ======================================================


    def _risk_level(
        self,
        score:int
    ) -> str:


        if score >=85:

            return "LOW"


        elif score >=60:

            return "MEDIUM"


        elif score >=30:

            return "HIGH"


        else:

            return "CRITICAL"





    # ======================================================
    # EXPLAINABILITY
    # ======================================================


    def _explainability(
        self,
        scores:Dict,
        issues:List[str],
        decision:str
    ) -> Dict:


        return {


            "scores":

            scores,


            "detected_issues":

            issues,


            "decision_reason":

            (
                "All checks passed"
                if not issues

                else

                "Problems detected during validation"
            ),


            "final_decision":

            decision

        }





    # ======================================================
    # SAVE VALIDATION HISTORY
    # ======================================================


    def _save_history(
        self,
        result:Dict
    ):


        os.makedirs(
            "data",
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

                +

                "\n"

            )





    # ======================================================
    # HUMAN FEEDBACK
    # ======================================================


    def save_feedback(
        self,
        email_id:str,
        agent_decision:str,
        human_decision:str,
        comment:str=""
    ):


        os.makedirs(
            "data",
            exist_ok=True
        )


        feedback = {

            "id":
            str(uuid.uuid4()),


            "email_id":
            email_id,


            "agent_decision":
            agent_decision,


            "human_decision":
            human_decision,


            "comment":
            comment,


            "timestamp":
            datetime.now().isoformat()

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

                +

                "\n"

            )





    # ======================================================
    # MAIN VALIDATION
    # ======================================================


    def validate(
        self,
        original_email:str,
        generated_response:str
    ) -> Dict:


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



        # Missing data protection

        if not original_email.strip() or not generated_response.strip():

            result = {

                "agent":
                self.name,


                "approved":
                False,


                "decision":
                "REJECTED",


                "action":
                "REGENERATE_RESPONSE",


                "risk":
                "CRITICAL",


                "issues":
                [
                    "Missing input data"
                ],

                "timestamp":
                datetime.now().isoformat()

            }


            self._save_history(result)

            return result





        ai = self._validate_with_ai(

            original_email,

            generated_response

        )




        # Ollama failure

        if not ai["success"]:

            result = {

                "agent":
                self.name,


                "approved":
                False,


                "decision":
                "NEEDS_REVIEW",


                "action":
                "HUMAN_REVIEW",


                "risk":
                "HIGH",


                "issues":
                [
                    "AI validation unavailable"
                ],


                "timestamp":
                datetime.now().isoformat()

            }


            self._save_history(result)

            return result





        final_score = self._calculate_final_score(

            rule["score"],

            ai["score"],

            security["score"],

            quality["score"]

        )




        issues = list(dict.fromkeys(

            rule["issues"]

            +

            ai["issues"]

            +

            quality["issues"]

            +

            security["risks"]

        ))





        semantic_pass = all([

            ai["relevant"],

            ai["answers_request"],

            ai["professional"],

            ai["complete"],

            not ai["contradiction"],

            not ai["hallucination"]

        ])





        decision = self._decision_engine(

            final_score,

            security["safe"],

            semantic_pass

        )





        result = {


            "agent":
            self.name,


            "timestamp":
            datetime.now().isoformat(),


            "confidence_score":
            final_score,


            "risk_level":
            self._risk_level(
                final_score
            ),


            "approved":
            decision["decision"]
            ==
            "APPROVED",


            "decision":
            decision["decision"],


            "action":
            decision["action"],



            "scores":{


                "rules":
                rule["score"],


                "ai":
                ai["score"],


                "security":
                security["score"],


                "quality":
                quality["score"]

            },


            "issues":
            issues,


            "explainability":
            self._explainability(

                {

                    "rules":
                    rule["score"],

                    "ai":
                    ai["score"],

                    "security":
                    security["score"],

                    "quality":
                    quality["score"]

                },

                issues,

                decision["decision"]

            )

        }



        self._save_history(result)


        return result
