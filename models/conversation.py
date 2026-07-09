"""Conversation domain models."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ConversationStatus(str, Enum):
    OPEN = "open"
    QUALIFIED = "qualified"
    CLOSED = "closed"
    SUPPRESSED = "suppressed"


class Message(BaseModel):
    role: str
    body: str
    message_sid: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    phone_number: str
    business_id: str
    messages: list[dict[str, Any]] = Field(default_factory=list)
    status: ConversationStatus = ConversationStatus.OPEN
    lead_extracted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
