from unittest.mock import AsyncMock, patch

import pytest

import handlers.missed_call as missed_call


def form(status="no-answer"):
    return {
        "CallStatus": status,
        "From": "+15559998888",
        "To": "+15551112222",
        "CallSid": "CA123",
    }


@pytest.mark.asyncio
async def test_missed_call_happy_path_sends_text_and_creates_thread():
    with patch.object(missed_call.supabase_client, "is_suppressed", new=AsyncMock(return_value=False)), \
         patch.object(missed_call.supabase_client, "recently_texted", new=AsyncMock(return_value=False)), \
         patch.object(missed_call.supabase_client, "recent_outbound_message_count", new=AsyncMock(return_value=0)), \
         patch.object(missed_call, "generate_missed_call_sms", new=AsyncMock(return_value="Sorry we missed you.")), \
         patch.object(missed_call.twilio_client, "send_sms", new=AsyncMock(return_value=True)) as send, \
         patch.object(missed_call.supabase_client, "log_missed_call", new=AsyncMock(return_value={})), \
         patch.object(missed_call.supabase_client, "create_conversation", new=AsyncMock(return_value={})) as create:
        result = await missed_call.handle_missed_call(form())

    assert result == {"status": "text_sent", "text_sent": True}
    send.assert_awaited_once()
    create.assert_awaited_once()


@pytest.mark.asyncio
async def test_missed_call_ignores_completed_status():
    result = await missed_call.handle_missed_call(form("completed"))

    assert result == {"status": "ignored", "reason": "call_status"}


@pytest.mark.asyncio
async def test_missed_call_duplicate_is_suppressed():
    with patch.object(missed_call.supabase_client, "is_suppressed", new=AsyncMock(return_value=False)), \
         patch.object(missed_call.supabase_client, "recently_texted", new=AsyncMock(return_value=True)), \
         patch.object(missed_call.supabase_client, "log_missed_call", new=AsyncMock(return_value={})), \
         patch.object(missed_call.twilio_client, "send_sms", new=AsyncMock()) as send:
        result = await missed_call.handle_missed_call(form())

    assert result["status"] == "duplicate_suppressed"
    send.assert_not_awaited()


@pytest.mark.asyncio
async def test_missed_call_rate_limit_blocks_sms():
    with patch.object(missed_call.supabase_client, "is_suppressed", new=AsyncMock(return_value=False)), \
         patch.object(missed_call.supabase_client, "recently_texted", new=AsyncMock(return_value=False)), \
         patch.object(missed_call.supabase_client, "recent_outbound_message_count", new=AsyncMock(return_value=3)), \
         patch.object(missed_call.supabase_client, "log_missed_call", new=AsyncMock(return_value={})), \
         patch.object(missed_call.twilio_client, "send_sms", new=AsyncMock()) as send:
        result = await missed_call.handle_missed_call(form())

    assert result["status"] == "rate_limited"
    send.assert_not_awaited()
