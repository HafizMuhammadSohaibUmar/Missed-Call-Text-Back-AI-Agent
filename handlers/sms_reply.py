"""Inbound SMS reply handling."""
from datetime import datetime, timedelta, timezone

from config import get_settings
from db.supabase import supabase_client
from integrations.twilio_client import twilio_client
from models.conversation import ConversationStatus, Message
from services.conversation import build_lead, exchange_count
from services.notifications import lead_confirmation, notify_owner
from services.qualification import qualify
from utils import is_stop_message, normalize_phone


async def handle_sms_reply(form: dict) -> dict:
    phone = normalize_phone(form.get("From", ""))
    body = form.get("Body", "").strip()
    message_sid = form.get("MessageSid", "")

    if is_stop_message(body):
        await supabase_client.suppress(phone, f"stop:{message_sid}")
        await twilio_client.send_sms(phone, "You are opted out and will not receive further texts.")
        return {"status": "suppressed"}

    if await supabase_client.is_suppressed(phone):
        return {"status": "suppressed"}

    if await supabase_client.message_sid_seen(phone, message_sid):
        return {"status": "duplicate_message"}

    conversation = await supabase_client.open_conversation(phone)
    if not conversation:
        conversation = await supabase_client.create_conversation(phone, [])

    conversation = await supabase_client.append_message(
        conversation,
        Message(role="user", body=body, message_sid=message_sid),
    )

    settings = get_settings()
    if exchange_count(conversation.get("messages") or []) >= settings.max_exchanges:
        reply = "Thanks. Please send the best callback number and we will follow up directly."
        await twilio_client.send_sms(phone, reply, context_id=conversation["id"])
        await supabase_client.append_message(conversation, Message(role="assistant", body=reply))
        await supabase_client.update_conversation(conversation["id"], status=ConversationStatus.CLOSED.value)
        return {"status": "closed_max_exchanges"}

    qualification = await qualify(conversation.get("messages") or [])
    reply = qualification["reply"]
    since = datetime.now(timezone.utc) - timedelta(hours=settings.duplicate_window_hours)
    if await supabase_client.recent_outbound_message_count(phone, since) >= settings.max_texts_per_window:
        await supabase_client.update_conversation(conversation["id"], status=ConversationStatus.CLOSED.value)
        return {"status": "rate_limited"}

    if qualification.get("complete"):
        lead = build_lead(conversation, qualification)
        await supabase_client.create_lead(lead)
        await notify_owner(lead)
        reply = lead_confirmation(lead)
        await twilio_client.send_sms(phone, reply, context_id=conversation["id"])
        await supabase_client.append_message(conversation, Message(role="assistant", body=reply))
        await supabase_client.update_conversation(
            conversation["id"],
            status=ConversationStatus.QUALIFIED.value,
            lead_extracted=True,
        )
        return {"status": "lead_created", "lead": lead.model_dump(mode="json")}

    await twilio_client.send_sms(phone, reply, context_id=conversation["id"])
    await supabase_client.append_message(conversation, Message(role="assistant", body=reply))
    return {"status": "reply_sent", "complete": False}
