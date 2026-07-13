import re
from typing import Dict


class SecurityValidator:

    def validate(self, response: str) -> Dict:

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
            if re.search(
                pattern,
                response,
                flags=re.IGNORECASE
            ):
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
