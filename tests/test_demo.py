from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app


def test_demo_page_loads():
    client = TestClient(app)
    response = client.get("/demo")

    assert response.status_code == 200
    assert "LeadPilot AI Missed Call Text-Back Agent" in response.text
    assert "Simulate Missed Call" in response.text


def test_demo_missed_call_returns_sms_preview():
    client = TestClient(app)
    with patch("handlers.demo.handle_missed_call", new=AsyncMock(return_value={
        "status": "text_sent",
        "text_sent": True,
        "sms_body": "Sorry we missed you.",
    })) as handler:
        response = client.post("/demo/missed-call", json={
            "caller_phone": "+15559998888",
            "call_status": "no-answer",
            "time_scenario": "morning",
        })

    body = response.json()
    assert response.status_code == 200
    assert body["sms_mode"] == "dry_run"
    assert body["sms_preview"][0]["label"] == "Missed-call text-back"
    handler.assert_awaited_once()


def test_demo_reply_complete_lead_returns_owner_and_customer_previews():
    client = TestClient(app)
    lead = {
        "id": "lead-1",
        "business_id": "test-business",
        "conversation_id": "conv-1",
        "phone_number": "+15559998888",
        "name": "Jane Doe",
        "service_type": "AC repair",
        "address": "123 Main Street",
        "urgency_level": "same_day",
        "created_at": "2026-07-09T00:00:00+00:00",
    }
    with patch("handlers.demo.handle_sms_reply", new=AsyncMock(return_value={
        "status": "lead_created",
        "lead": lead,
    })):
        response = client.post("/demo/reply", json={
            "caller_phone": "+15559998888",
            "reply_scenario": "complete",
            "reply_body": "Need AC repair at 123 Main Street",
        })

    body = response.json()
    assert response.status_code == 200
    assert len(body["sms_preview"]) == 2
    assert body["sms_preview"][0]["label"] == "Owner alert preview"
    assert body["sms_preview"][1]["label"] == "Customer confirmation"


def test_demo_reply_stop_returns_opt_out_preview():
    client = TestClient(app)
    with patch("handlers.demo.handle_sms_reply", new=AsyncMock(return_value={"status": "suppressed"})):
        response = client.post("/demo/reply", json={
            "caller_phone": "+15559998888",
            "reply_scenario": "stop",
        })

    body = response.json()
    assert response.status_code == 200
    assert body["sms_preview"][0]["label"] == "Opt-out confirmation"
