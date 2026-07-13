class ScoreCalculator:

    @staticmethod
    def calculate(
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
