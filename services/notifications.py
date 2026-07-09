"""Owner and lead notifications."""
from config import get_settings
from integrations.twilio_client import twilio_client
from models.lead import LeadRecord


def owner_lead_alert(lead: LeadRecord) -> str:
    settings = get_settings()
    return (
        f"New missed-call lead for {settings.business_name}: {lead.name}, {lead.phone_number}, "
        f"{lead.service_type}, {lead.address}, urgency={lead.urgency_level.value}."
    )


def lead_confirmation(lead: LeadRecord) -> str:
    settings = get_settings()
    return (
        f"Thanks {lead.name}. We have your {lead.service_type} request for {lead.address}. "
        f"{settings.owner_first_name} or the team will follow up soon. - {settings.business_name}"
    )


async def notify_owner(lead: LeadRecord) -> bool:
    settings = get_settings()
    return await twilio_client.send_sms(settings.owner_phone_number, owner_lead_alert(lead),
                                        context_id=lead.conversation_id)
