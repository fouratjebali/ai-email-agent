import re
from typing import List


class TextUtils:

    @staticmethod
    def extract_words(text: str) -> List[str]:
        return re.findall(
            r"\b\w+\b",
            text.lower(),
            flags=re.UNICODE
        )

    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        return [
            sentence.strip()
            for sentence in re.split(r"[.!?]+", text)
            if sentence.strip()
        ]
