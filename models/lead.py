"""Lead models."""
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class UrgencyLevel(str, Enum):
    EMERGENCY = "emergency"
    SAME_DAY = "same_day"
    SOON = "soon"
    FLEXIBLE = "flexible"
    UNKNOWN = "unknown"


class LeadRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    business_id: str
    conversation_id: str
    phone_number: str
    name: str
    service_type: str
    address: str
    urgency_level: UrgencyLevel
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
