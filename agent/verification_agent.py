from datetime import datetime
from typing import Dict, List
import json
import os
import re
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import settings
class ResponseValidatorAgent:
    """
    Agent 2:
    Hybrid email response validator.

    Features:
    - Rule based validation
    - Ollama semantic validation
    - Risk assessment
    - Explainability report
    - Human feedback storage
    - Security checks
    """


    def __init__(
        self,
        confidence_threshold: int = 80
    ):

        self.name = "Response Validator Agent"

        self.confidence_threshold = confidence_threshold

        self.llm = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0,
            num_predict=500,
            client_kwargs={
                "timeout": settings.OLLAMA_TIMEOUT_SECONDS
            }
        )


    # ======================================================
    # TEXT UTILITIES
    # ======================================================


    def _extract_words(
        self,
        text: str
    ) -> List[str]:

        return re.findall(
            r"\b\w+\b",
            text.lower(),
            flags=re.UNICODE
        )


    def _extract_sentences(
        self,
        text: str
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
    # SECURITY CHECK
    # ======================================================


    def _security_check(
        self,
        response: str
    ) -> Dict:


        patterns = [

            r"password\s*[:=]\s*\S+",

            r"api[_\s-]?key\s*[:=]\s*\S+",

            r"secret\s*[:=]\s*\S+",

            r"access[_\s-]?token\s*[:=]\s*\S+",

            r"bearer\s+[a-zA-Z0-9._\-]+",

            r"-----BEGIN PRIVATE KEY-----",

            r"\b\d{16}\b"
        ]


        for pattern in patterns:

            if re.search(
                pattern,
                response,
                flags=re.IGNORECASE
            ):

                return {
                    "safe": False,
                    "issue":
                    "Sensitive information detected"
                }


        return {
            "safe": True,
            "issue": None
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

            issues.append(
                "Original email missing"
            )

            suggestions.append(
                "Provide original email"
            )

            score -= 40



        if not generated_response.strip():

            issues.append(
                "Generated response empty"
            )

            suggestions.append(
                "Generate a valid response"
            )

            score -= 60


            return {
                "score": max(score,0),
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



        # Length check

        if word_count < 5:

            issues.append(
                "Response too short"
            )

            suggestions.append(
                "Provide more details"
            )

            score -=20



        elif word_count < 10:

            issues.append(
                "Response may lack details"
            )

            score -=5



        # Sentence check

        if not sentences:

            issues.append(
                "No complete sentence"
            )

            score -=10



        else:

            average = (
                word_count /
                len(sentences)
            )


            if average < 2:

                issues.append(
                    "Fragmented response"
                )

                score -=10



        # Security

        security = self._security_check(
            generated_response
        )


        if not security["safe"]:

            issues.append(
                security["issue"]
            )

            suggestions.append(
                "Remove sensitive information"
            )

            score -=30



        # Repetition

        if word_count >=20:

            ratio = (
                len(set(words))
                /
                word_count
            )


            if ratio <0.35:

                issues.append(
                    "Excessive repetition"
                )

                score -=10



        return {

            "score":
            max(0,min(score,100)),

            "issues":
            issues,
            "suggestions":
            suggestions
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

You are a strict email response validation agent.

Analyze the generated response compared to the original email.

Check:

- relevance
- answering the request
- professional tone
- clarity
- contradictions
- invented information
- unsafe content

Return ONLY JSON.

Format:

{
 "score":0,
 "relevant":true,
 "answers_request":true,
 "professional":true,
 "clear":true,
 "contradiction_detected":false,
 "unsupported_claims_detected":false,
 "issues":[],
 "suggestions":[]
}

Score must be between 0 and 100.

No markdown.
No explanation.

"""


        user_prompt = f"""

ORIGINAL EMAIL:

{original_email}


GENERATED RESPONSE:

{generated_response}

"""


        # Retry mechanism

        attempts = 2


        for attempt in range(attempts):

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
                    r"^```(?:json)?\s*",
                    "",
                    content,
                    flags=re.IGNORECASE
                )


                content = re.sub(
                    r"\s*```$",
                    "",
                    content
                )



                data = json.loads(
                    content
                )



                score = int(
                    data.get(
                        "score",
                        0
                    )
                )


                return {

                    "success":True,

                    "score":
                    max(
                        0,
                        min(
                            score,
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


                    "clear":
                    bool(
                        data.get(
                            "clear",
                            False
                        )
                    ),


                    "contradiction_detected":
                    bool(
                        data.get(
                            "contradiction_detected",
                            False
                        )
                    ),


                    "unsupported_claims_detected":
                    bool(
                        data.get(
                            "unsupported_claims_detected",
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



            except Exception as error:


                if attempt == attempts-1:

                    return {

                        "success":False,

                        "score":0,

                        "issues":[
                            "Ollama validation failed"
                        ],

                        "suggestions":[
                            "Manual review required"
                        ],

                        "error":
                        str(error)
                    }



    # ======================================================
    # RISK LEVEL
    # ======================================================


    def _calculate_risk_level(
        self,
        score:int,
        issues:List[str]
    ) -> str:


        if score >=85 and not issues:

            return "LOW"


        elif score >=60:

            return "MEDIUM"


        else:

            return "HIGH"



    # ======================================================
    # EXPLAINABILITY
    # ======================================================


    def _generate_explanation(
        self,
        rule_score,
        ai_score,
        issues
    ):


        if not issues:

            decision = (
                "All validation checks passed"
            )

        else:

            decision = (
                "Review required because "
                "problems were detected"
            )



        return {

            "rule_analysis":
            f"Rule validation score: {rule_score}/100",


            "ai_analysis":
            f"Semantic AI score: {ai_score}/100",


            "detected_problems":
            issues,


            "final_decision":
            decision
        }



    # ======================================================
    # HUMAN FEEDBACK STORAGE
    # ======================================================


    def save_feedback(
        self,
        email_id:str,
        agent_result:str,
        human_decision:str,
        comment:str=""
    ):


        os.makedirs(
            "data",
            exist_ok=True
        )


        feedback = {

            "email_id":
            email_id,


            "agent_result":
            agent_result,


            "human_decision":
            human_decision,


            "comment":
            comment,


            "timestamp":
            datetime.now().isoformat()

        }



        with open(
            "data/feedback.json",
            "a",
            encoding="utf-8"
        ) as file:


            file.write(
                json.dumps(feedback)
                + "\n"
            )
    # ======================================================
    # MAIN VALIDATION
    # ======================================================


    def validate(
        self,
        original_email:str,
        generated_response:str
    ) -> Dict:


        # 1) Rule validation

        rule_result = self._validate_rules(
            original_email,
            generated_response
        )



        # Critical missing data

        if (
            not original_email.strip()
            or not generated_response.strip()
        ):


            risk = self._calculate_risk_level(
                rule_result["score"],
                rule_result["issues"]
            )


            return {

                "agent":
                self.name,


                "timestamp":
                datetime.now().isoformat(),


                "approved":
                False,


                "confidence_score":
                rule_result["score"],


                "risk_level":
                risk,


                "rule_score":
                rule_result["score"],


                "ai_score":
                None,


                "explainability":
                self._generate_explanation(
                    rule_result["score"],
                    None,
                    rule_result["issues"]
                ),


                "issues":
                rule_result["issues"],


                "suggestions":
                rule_result["suggestions"],


                "action":
                "REVIEW_REQUIRED"
            }




        # 2) AI validation


        ai_result = self._validate_with_ai(
            original_email,
            generated_response
        )



        # Ollama failure


        if not ai_result["success"]:


            issues = list(dict.fromkeys(
                rule_result["issues"]
                +
                ai_result["issues"]
            ))



            risk = self._calculate_risk_level(
                rule_result["score"],
                issues
            )



            return {

                "agent":
                self.name,


                "timestamp":
                datetime.now().isoformat(),


                "approved":
                False,


                "confidence_score":
                rule_result["score"],


                "risk_level":
                risk,


                "rule_score":
                rule_result["score"],


                "ai_score":
                None,


                "explainability":
                self._generate_explanation(
                    rule_result["score"],
                    None,
                    issues
                ),


                "issues":
                issues,


                "suggestions":
                ai_result["suggestions"],


                "action":
                "REVIEW_REQUIRED"
            }




        # 3) Hybrid score


        final_score = round(
            (
                rule_result["score"]
                *
                0.40
            )
            +
            (
                ai_result["score"]
                *
                0.60
            )
        )



        # Merge issues


        issues = list(dict.fromkeys(

            rule_result["issues"]
            +
            ai_result["issues"]

        ))



        suggestions = list(dict.fromkeys(

            rule_result["suggestions"]
            +
            ai_result["suggestions"]

        ))



        # 4) Semantic checks


        semantic_pass = all([

            ai_result["relevant"],

            ai_result["answers_request"],

            ai_result["professional"],

            ai_result["clear"],

            not ai_result["contradiction_detected"],

            not ai_result["unsupported_claims_detected"]

        ])




        approved = (

            final_score
            >=
            self.confidence_threshold

            and

            semantic_pass

        )



        # 5) Risk calculation


        risk = self._calculate_risk_level(
            final_score,
            issues
        )



        # 6) Final response


        return {


            "agent":
            self.name,


            "timestamp":
            datetime.now().isoformat(),



            "approved":
            approved,



            "confidence_score":
            final_score,



            "risk_level":
            risk,



            "rule_score":
            rule_result["score"],



            "ai_score":
            ai_result["score"],



            "semantic_checks":{


                "relevant":
                ai_result["relevant"],


                "answers_request":
                ai_result["answers_request"],


                "professional":
                ai_result["professional"],


                "clear":
                ai_result["clear"],


                "contradiction_detected":
                ai_result["contradiction_detected"],


                "unsupported_claims_detected":
                ai_result["unsupported_claims_detected"]

            },



            "explainability":
            self._generate_explanation(
                rule_result["score"],
                ai_result["score"],
                issues
            ),



            "issues":
            issues,



            "suggestions":
            suggestions,



            "action":
            (
                "SEND_EMAIL"
                if approved
                else
                "REVIEW_REQUIRED"
            )

        }
