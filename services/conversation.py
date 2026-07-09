"""Conversation orchestration."""
from models.conversation import ConversationStatus, Message
from models.lead import LeadRecord, UrgencyLevel
from services.notifications import lead_confirmation, notify_owner


def exchange_count(messages: list[dict]) -> int:
    return sum(1 for message in messages if message.get("role") == "user")


def build_lead(conversation: dict, qualification: dict) -> LeadRecord:
    return LeadRecord(
        business_id=conversation["business_id"],
        conversation_id=conversation["id"],
        phone_number=conversation["phone_number"],
        name=qualification["name"],
        service_type=qualification["service_type"],
        address=qualification["address"],
        urgency_level=UrgencyLevel(qualification["urgency_level"]),
    )
