from datetime import datetime
from typing import Iterable

SEVERITY_WEIGHTS = {
    "high-fever": 2.0,
    "fever": 1.2,
    "bleeding": 2.5,
    "asphyxia": 3.0,
    "convulsions": 3.0,
    "seizures": 3.0,
    "breathing-difficulty": 2.8,
    "dyspnea": 2.2,
    "tachypnoea": 2.2,
    "jaundice": 2.0,
    "abortion": 2.3,
    "anorexia": 1.0,
}

ESCALATION_THRESHOLDS = {
    "critical": 7.0,
    "high": 4.5,
    "moderate": 2.5,
}

CONTRAINDICATION_MAP = {
    "pregnant": "Avoid tetracyclines/fluoroquinolones unless explicitly advised by a licensed veterinarian.",
    "calf": "Adjust dose carefully for young calves; monitor hydration and rumen function.",
}

WITHDRAWAL_MAP = {
    "mastitis": "Milk withdrawal: typically 72-96 hours depending on intramammary antibiotic label.",
    "pneumonia": "Meat withdrawal: verify antibiotic-specific period (often 7-28 days).",
    "brucellosis": "Do not use milk for consumption until veterinarian/public-health clearance.",
}


def _tokenize_symptoms(text: str) -> list[str]:
    return [item.strip().lower() for item in text.split(",") if item.strip()]


def normalize_symptoms(text: str, known_symptoms: Iterable[str]) -> tuple[str, list[str]]:
    tokens = _tokenize_symptoms(text)
    known = {s.lower() for s in known_symptoms}
    normalized = []
    unknown = []

    for token in tokens:
        normalized_token = token.replace("_", "-").replace(" ", "-")
        if normalized_token in known:
            normalized.append(normalized_token)
        elif token in known:
            normalized.append(token)
        else:
            unknown.append(token)

    deduped = []
    for token in normalized:
        if token not in deduped:
            deduped.append(token)

    return ",".join(deduped), unknown


def severity_from_symptoms(symptoms_text: str) -> tuple[float, str]:
    tokens = _tokenize_symptoms(symptoms_text)
    score = 0.0
    for token in tokens:
        score += SEVERITY_WEIGHTS.get(token, 0.4)

    if score >= ESCALATION_THRESHOLDS["critical"]:
        return round(score, 2), "critical"
    if score >= ESCALATION_THRESHOLDS["high"]:
        return round(score, 2), "high"
    if score >= ESCALATION_THRESHOLDS["moderate"]:
        return round(score, 2), "moderate"
    return round(score, 2), "normal"


def severity_from_query_text(query_text: str) -> tuple[float, str]:
    rough = query_text.lower().replace(" ", "-")
    tokens = [word.strip(".,!?") for word in rough.split("-") if word]
    score = 0.0
    for token in tokens:
        score += SEVERITY_WEIGHTS.get(token, 0.05)

    if "urgent" in query_text.lower() or "emergency" in query_text.lower():
        score += 2.0

    if score >= 4.5:
        return round(score, 2), "high"
    if score >= 2.0:
        return round(score, 2), "moderate"
    return round(score, 2), "normal"


def season_from_date(value: datetime) -> str:
    month = value.month
    if month in (3, 4, 5):
        return "summer"
    if month in (6, 7, 8, 9):
        return "monsoon"
    if month in (10, 11):
        return "post_monsoon"
    return "winter"


def build_prescription_guidance(
    diagnosis: str,
    treatment: str,
    weight_kg: float | None,
    pregnancy_status: str | None,
) -> dict:
    final_weight = weight_kg if weight_kg and weight_kg > 0 else 350.0
    base_dose_ml = round((final_weight / 10.0) * 0.2, 2)

    disease_key = (diagnosis or "").strip().lower()
    withdrawal = WITHDRAWAL_MAP.get(disease_key, "Check label-specific withdrawal before milk/meat consumption.")

    warnings = []
    if pregnancy_status and pregnancy_status.lower() == "pregnant":
        warnings.append(CONTRAINDICATION_MAP["pregnant"])
    if final_weight < 120:
        warnings.append(CONTRAINDICATION_MAP["calf"])

    if "consult" in treatment.lower():
        warnings.append("Treatment requires in-person veterinary confirmation before administration.")

    return {
        "estimated_weight_kg": final_weight,
        "suggested_dose_ml": base_dose_ml,
        "withdrawal_period": withdrawal,
        "contraindications": warnings,
    }
