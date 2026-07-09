"""Missed-call webhook handling."""
from datetime import datetime, timedelta, timezone

from config import get_settings
from db.supabase import supabase_client
from integrations.twilio_client import twilio_client
from models.conversation import Message
from services.sms_generator import generate_missed_call_sms
from utils import normalize_phone


async def handle_missed_call(form: dict, sms_override: str | None = None) -> dict:
    status = (form.get("CallStatus") or "").lower()
    from_number = normalize_phone(form.get("From", ""))
    to_number = normalize_phone(form.get("To", ""))
    call_sid = form.get("CallSid", "")

    if status not in {"no-answer", "busy"}:
        return {"status": "ignored", "reason": "call_status"}

    if await supabase_client.is_suppressed(from_number):
        await supabase_client.log_missed_call(
            from_number=from_number, to_number=to_number, call_sid=call_sid,
            text_sent=False, duplicate_suppressed=False,
        )
        return {"status": "suppressed"}

    settings = get_settings()
    since = datetime.now(timezone.utc) - timedelta(hours=settings.duplicate_window_hours)
    if await supabase_client.recently_texted(from_number, since):
        await supabase_client.log_missed_call(
            from_number=from_number, to_number=to_number, call_sid=call_sid,
            text_sent=False, duplicate_suppressed=True,
        )
        return {"status": "duplicate_suppressed"}

    if await supabase_client.recent_outbound_message_count(from_number, since) >= settings.max_texts_per_window:
        await supabase_client.log_missed_call(
            from_number=from_number, to_number=to_number, call_sid=call_sid,
            text_sent=False, duplicate_suppressed=True,
        )
        return {"status": "rate_limited"}

    body = sms_override or await generate_missed_call_sms()
    sent = await twilio_client.send_sms(from_number, body, context_id=call_sid)
    await supabase_client.log_missed_call(
        from_number=from_number, to_number=to_number, call_sid=call_sid,
        text_sent=sent, duplicate_suppressed=False,
    )
    if sent:
        await supabase_client.create_conversation(
            from_number,
            [Message(role="assistant", body=body)],
        )
    return {"status": "text_sent" if sent else "send_failed", "text_sent": sent, "sms_body": body}
