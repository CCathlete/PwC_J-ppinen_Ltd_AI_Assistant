from pydantic import BaseModel, ConfigDict
from enum import Enum
from typing import Final

MODEL_NAME: Final[str] = "jappinen-maintenance-assistant"

class SafetyStatus(Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    NOT_FOUND = "not_found"

class AuditedResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    answer: str
    status: SafetyStatus
    confidence_score: float
