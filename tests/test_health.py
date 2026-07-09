from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app


def test_health_includes_last_10_call_stats():
    client = TestClient(app)
    with patch("main.supabase_client.health_check", new=AsyncMock(return_value={"ok": True})), \
         patch("main.twilio_client.health_check", new=AsyncMock(return_value={"ok": True, "mode": "dry_run"})), \
         patch("main.supabase_client.last_10_calls_stats", new=AsyncMock(return_value={
             "count": 2,
             "texts_sent": 1,
             "duplicate_suppressed": 1,
         })):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["last_10_calls"]["count"] == 2
