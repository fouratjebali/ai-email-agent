import json
import os
from typing import Dict


class HistoryManager:

    def __init__(
        self,
        history_file: str = "data/validation_history.json"
    ):
        self.history_file = history_file

    def save(self, result: Dict) -> None:

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
