import json
import os
import uuid
from datetime import datetime
from typing import Dict


class FeedbackManager:

    def __init__(
        self,
        feedback_file: str = "data/feedback.json"
    ):
        self.feedback_file = feedback_file

    def save(
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
