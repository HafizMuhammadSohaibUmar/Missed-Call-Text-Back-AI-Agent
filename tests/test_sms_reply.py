from unittest.mock import AsyncMock, patch

import pytest

import handlers.sms_reply as sms_reply
from models.conversation import ConversationStatus


def form(body="Need AC repair at 123 Main St today"):
    return {
        "From": "+15559998888",
        "Body": body,
        "MessageSid": "SM123",
    }


@pytest.mark.asyncio
async def test_sms_reply_creates_lead_when_qualification_complete():
    conversation = {
        "id": "conv-1",
        "business_id": "test-business",
        "phone_number": "+15559998888",
        "messages": [],
    }
    appended = {
        **conversation,
        "messages": [{"role": "user", "body": "Need AC repair", "message_sid": "SM123"}],
    }
    qualification = {
        "complete": True,
        "name": "Jane Doe",
        "service_type": "AC repair",
        "address": "123 Main St",
        "urgency_level": "same_day",
        "reply": "Thanks, we have what we need.",
    }
    with patch.object(sms_reply.supabase_client, "is_suppressed", new=AsyncMock(return_value=False)), \
         patch.object(sms_reply.supabase_client, "message_sid_seen", new=AsyncMock(return_value=False)), \
         patch.object(sms_reply.supabase_client, "open_conversation", new=AsyncMock(return_value=conversation)), \
         patch.object(sms_reply.supabase_client, "append_message", new=AsyncMock(return_value=appended)), \
         patch.object(sms_reply, "qualify", new=AsyncMock(return_value=qualification)), \
         patch.object(sms_reply.supabase_client, "recent_outbound_message_count", new=AsyncMock(return_value=0)), \
         patch.object(sms_reply.supabase_client, "create_lead", new=AsyncMock(return_value={})), \
         patch.object(sms_reply, "notify_owner", new=AsyncMock(return_value=True)), \
         patch.object(sms_reply.twilio_client, "send_sms", new=AsyncMock(return_value=True)), \
         patch.object(sms_reply.supabase_client, "update_conversation", new=AsyncMock()) as update:
        result = await sms_reply.handle_sms_reply(form())

    assert result["status"] == "lead_created"
    update.assert_awaited_with("conv-1", status=ConversationStatus.QUALIFIED.value, lead_extracted=True)


@pytest.mark.asyncio
async def test_sms_reply_failure_path_duplicate_message_sid():
    with patch.object(sms_reply.supabase_client, "is_suppressed", new=AsyncMock(return_value=False)), \
         patch.object(sms_reply.supabase_client, "message_sid_seen", new=AsyncMock(return_value=True)), \
         patch.object(sms_reply.twilio_client, "send_sms", new=AsyncMock()) as send:
        result = await sms_reply.handle_sms_reply(form())

    assert result == {"status": "duplicate_message"}
    send.assert_not_awaited()


@pytest.mark.asyncio
async def test_sms_reply_rate_limit_closes_conversation():
    conversation = {
        "id": "conv-1",
        "business_id": "test-business",
        "phone_number": "+15559998888",
        "messages": [],
    }
    appended = {
        **conversation,
        "messages": [{"role": "user", "body": "Need AC repair", "message_sid": "SM123"}],
    }
    with patch.object(sms_reply.supabase_client, "is_suppressed", new=AsyncMock(return_value=False)), \
         patch.object(sms_reply.supabase_client, "message_sid_seen", new=AsyncMock(return_value=False)), \
         patch.object(sms_reply.supabase_client, "open_conversation", new=AsyncMock(return_value=conversation)), \
         patch.object(sms_reply.supabase_client, "append_message", new=AsyncMock(return_value=appended)), \
         patch.object(sms_reply, "qualify", new=AsyncMock(return_value={"complete": False, "reply": "What address?"})), \
         patch.object(sms_reply.supabase_client, "recent_outbound_message_count", new=AsyncMock(return_value=3)), \
         patch.object(sms_reply.supabase_client, "update_conversation", new=AsyncMock()) as update, \
         patch.object(sms_reply.twilio_client, "send_sms", new=AsyncMock()) as send:
        result = await sms_reply.handle_sms_reply(form())

    assert result == {"status": "rate_limited"}
    update.assert_awaited_once_with("conv-1", status=ConversationStatus.CLOSED.value)
    send.assert_not_awaited()
