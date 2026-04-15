from services.clinical_service import normalize_symptoms, severity_from_query_text, severity_from_symptoms
from services.prediction_service import PredictionService


def test_normalize_symptoms_filters_unknown():
    normalized, unknown = normalize_symptoms("fever, high fever, weird-token", PredictionService.SYMPTOMS)
    assert "fever" in normalized
    assert "weird-token" in unknown


def test_severity_from_symptoms_increases_for_critical_signs():
    score, level = severity_from_symptoms("high-fever,asphyxia,convulsions")
    assert score > 0
    assert level in {"high", "critical"}


def test_query_severity_detects_urgency():
    score, level = severity_from_query_text("Emergency case with bleeding and fever")
    assert score > 0
    assert level in {"moderate", "high"}
