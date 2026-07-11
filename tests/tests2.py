import pytest

from agents.verification_agent import ResponseValidatorAgent


@pytest.fixture
def validator():
    return ResponseValidatorAgent()


def test_response_validation_success(validator):

    result = validator.validate(
        original_email="Bonjour, je veux connaître le prix du produit.",
        generated_response="Bonjour, le prix du produit est 100 dinars."
    )

    assert isinstance(result, dict)

    assert "risk_level" in result
    assert "score" in result
    assert "explanation" in result



def test_empty_original_email(validator):

    result = validator.validate(
        original_email="",
        generated_response="Bonjour voici la réponse."
    )

    assert result["risk_level"] == "HIGH"



def test_empty_generated_response(validator):

    result = validator.validate(
        original_email="Bonjour je veux une information.",
        generated_response=""
    )

    assert result["risk_level"] == "HIGH"



def test_validation_report_structure(validator):

    result = validator.validate(
        original_email="Demande de rendez-vous.",
        generated_response="Votre rendez-vous est confirmé."
    )

    assert "risk_level" in result
    assert "score" in result
    assert "explanation" in result



def test_agent2_no_crash(validator):

    result = validator.validate(
        original_email="Test email",
        generated_response="Test response"
    )

    assert result is not None
    assert isinstance(result, dict)



def test_score_range(validator):

    result = validator.validate(
        original_email="Question simple",
        generated_response="Réponse simple"
    )

    assert isinstance(result["score"], (int, float))

    assert 0 <= result["score"] <= 100
