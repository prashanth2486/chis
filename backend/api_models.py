from typing import Any, Optional

from pydantic import BaseModel


class RootResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    env: str


class ReadyResponse(BaseModel):
    status: str
    database: str
    uploads: str


class LoginResponse(BaseModel):
    user_id: str
    role: str
    name: str
    access_token: str
    token_type: str


class PredictResponse(BaseModel):
    symptoms: str
    predicted_disease: str
    recommended_treatment: str


class EclatRule(BaseModel):
    lhs: str
    rhs: str
    confidence: float


class EclatRunResponse(BaseModel):
    transaction_count: int
    frequent_items_count: int
    frequent_items: dict[str, str]
    rules_count: int
    strong_rules: list[EclatRule]


class GenericMessageResponse(BaseModel):
    message: str


class GenericDictResponse(BaseModel):
    data: dict[str, Any]


class ErrorMeta(BaseModel):
    request_id: str
    status_code: int
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorMeta
