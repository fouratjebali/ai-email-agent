import pytest

from agents.agent_2_response_validator import ResponseValidatorAgent


@pytest.fixture
def validator():
    """
    Create Agent 2 instance for tests
    """
    return ResponseValidatorAgent()


# ======================================================
# TEST 1 : Normal validation
# ======================================================

def test_response_validation_success(validator):

    result = validator.validate(
        original_email="""
        Bonjour,
        Je veux connaître le prix du produit.
        """,

        generated_response="""
        Bonjour,
        Le prix du produit est de 100 dinars.
        Merci.
        """
    )

    assert isinstance(result, dict)

    assert "risk_level" in result
    assert "score" in result
    assert "explanation" in result

    assert result["risk_level"] in [
        "LOW",
        "MEDIUM",
        "HIGH"
    ]



# ======================================================
# TEST 2 : Empty email
# ======================================================

def test_empty_original_email(validator):

    result = validator.validate(
        original_email="",

        generated_response="""
        Bonjour,
        Voici votre réponse.
        """
    )

    assert isinstance(result, dict)

    assert result["risk_level"] == "HIGH"



# ======================================================
# TEST 3 : Empty generated response
# ======================================================

def test_empty_generated_response(validator):

    result = validator.validate(
        original_email="""
        Bonjour,
        Je veux une information.
        """,

        generated_response=""
    )

    assert isinstance(result, dict)

    assert result["risk_level"] == "HIGH"



# ======================================================
# TEST 4 : Missing information detection
# ======================================================

def test_response_without_context(validator):

    result = validator.validate(
        original_email="""
        Bonjour,
        Je veux savoir si ma commande est disponible.
        """,

        generated_response="""
        Bonjour,
        Merci pour votre message.
        """
    )

    assert "risk_level" in result
    assert "explanation" in result



# ======================================================
# TEST 5 : Output structure validation
# ======================================================

def test_validation_output_structure(validator):

    result = validator.validate(
        original_email="""
        Demande de rendez-vous.
        """,

        generated_response="""
        Votre rendez-vous est confirmé pour demain.
        """
    )


    required_fields = [
        "risk_level",
        "score",
        "explanation"
    ]


    for field in required_fields:
        assert field in result



# ======================================================
# TEST 6 : Fail safe if AI unavailable
# ======================================================

def test_ollama_failure_safe(validator):

    try:

        result = validator.validate(
            original_email="""
            Test email.
            """,

            generated_response="""
            Test response.
            """
        )

        assert result is not None
        assert isinstance(result, dict)


    except Exception as error:

        pytest.fail(
            f"Agent 2 crashed : {error}"
        )



# ======================================================
# TEST 7 : Score validation
# ======================================================

def test_score_range(validator):

    result = validator.validate(
        original_email="""
        Question simple.
        """,

        generated_response="""
        Réponse simple.
        """
    )


    assert isinstance(
        result["score"],
        (int, float)
    )


    assert 0 <= result["score"] <= 100
