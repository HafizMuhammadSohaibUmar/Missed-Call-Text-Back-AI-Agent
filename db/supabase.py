"""Async Supabase PostgREST client."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from config import get_settings
from models.conversation import ConversationRecord, ConversationStatus, Message
from models.lead import LeadRecord


def _mask_phone(phone: str | None) -> str:
    if not phone:
        return ""
    return f"{phone[:3]}***{phone[-4:]}" if len(phone) >= 7 else "***"


class SupabaseClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.supabase_url.rstrip("/")
        self.business_id = settings.business_id
        self.headers = {
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {settings.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _url(self, table: str) -> str:
        return f"{self.base_url}/rest/v1/{table}"

    async def _request(self, method: str, table: str, *,
                       params: Optional[dict] = None,
                       json: Any = None) -> List[Dict]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(
                method, self._url(table), headers=self.headers, params=params, json=json
            )
            response.raise_for_status()
        return response.json() if response.content else []

    async def is_suppressed(self, phone: str) -> bool:
        rows = await self._request(
            "GET", "suppression_list",
            params={
                "business_id": f"eq.{self.business_id}",
                "phone_number": f"eq.{phone}",
                "select": "phone_number",
                "limit": "1",
            },
        )
        return bool(rows)

    async def suppress(self, phone: str, reason: str) -> None:
        if await self.is_suppressed(phone):
            return
        await self._request(
            "POST", "suppression_list",
            json={"business_id": self.business_id, "phone_number": phone, "reason": reason},
        )

    async def recent_text_count(self, phone: str, since: datetime) -> int:
        rows = await self._request(
            "GET", "missed_calls",
            params={
                "business_id": f"eq.{self.business_id}",
                "from_number": f"eq.{phone}",
                "text_sent": "eq.true",
                "text_sent_at": f"gte.{since.isoformat()}",
                "select": "id",
            },
        )
        return len(rows)

    async def recent_outbound_message_count(self, phone: str, since: datetime) -> int:
        rows = await self._request(
            "GET", "conversations",
            params={
                "business_id": f"eq.{self.business_id}",
                "phone_number": f"eq.{phone}",
                "last_message_at": f"gte.{since.isoformat()}",
                "select": "messages",
            },
        )
        count = await self.recent_text_count(phone, since)
        for row in rows:
            for message in row.get("messages") or []:
                if message.get("role") != "assistant":
                    continue
                raw_created_at = message.get("created_at")
                if not raw_created_at:
                    continue
                created_at = datetime.fromisoformat(str(raw_created_at).replace("Z", "+00:00"))
                if created_at >= since:
                    count += 1
        return count

    async def recently_texted(self, phone: str, since: datetime) -> bool:
        return await self.recent_text_count(phone, since) > 0

    async def log_missed_call(self, *, from_number: str, to_number: str, call_sid: str,
                              text_sent: bool, duplicate_suppressed: bool) -> dict:
        rows = await self._request(
            "POST", "missed_calls",
            json={
                "business_id": self.business_id,
                "from_number": from_number,
                "to_number": to_number,
                "call_sid": call_sid,
                "text_sent": text_sent,
                "text_sent_at": datetime.now(timezone.utc).isoformat() if text_sent else None,
                "duplicate_suppressed": duplicate_suppressed,
            },
        )
        return rows[0] if rows else {}

    async def open_conversation(self, phone: str) -> dict | None:
        rows = await self._request(
            "GET", "conversations",
            params={
                "business_id": f"eq.{self.business_id}",
                "phone_number": f"eq.{phone}",
                "status": f"eq.{ConversationStatus.OPEN.value}",
                "order": "last_message_at.desc",
                "limit": "1",
                "select": "*",
            },
        )
        return rows[0] if rows else None

    async def create_conversation(self, phone: str, messages: list[Message]) -> dict:
        record = ConversationRecord(
            business_id=self.business_id,
            phone_number=phone,
            messages=[m.model_dump(mode="json") for m in messages],
        )
        rows = await self._request("POST", "conversations", json=record.model_dump(mode="json"))
        return rows[0] if rows else {}

    async def append_message(self, conversation: dict, message: Message) -> dict:
        messages = list(conversation.get("messages") or [])
        messages.append(message.model_dump(mode="json"))
        rows = await self._request(
            "PATCH", "conversations",
            params={"id": f"eq.{conversation['id']}", "business_id": f"eq.{self.business_id}"},
            json={"messages": messages, "last_message_at": datetime.now(timezone.utc).isoformat()},
        )
        return rows[0] if rows else {**conversation, "messages": messages}

    async def update_conversation(self, conversation_id: str, **fields: Any) -> None:
        await self._request(
            "PATCH", "conversations",
            params={"id": f"eq.{conversation_id}", "business_id": f"eq.{self.business_id}"},
            json=fields,
        )

    async def message_sid_seen(self, phone: str, message_sid: str) -> bool:
        if not message_sid:
            return False
        rows = await self._request(
            "GET", "conversations",
            params={
                "business_id": f"eq.{self.business_id}",
                "phone_number": f"eq.{phone}",
                "select": "messages",
                "order": "last_message_at.desc",
                "limit": "3",
            },
        )
        for row in rows:
            for message in row.get("messages") or []:
                if message.get("message_sid") == message_sid:
                    return True
        return False

    async def create_lead(self, lead: LeadRecord) -> dict:
        rows = await self._request("POST", "leads", json=lead.model_dump(mode="json"))
        return rows[0] if rows else {}

    async def close_timed_out_conversations(self, before: datetime) -> int:
        rows = await self._request(
            "GET", "conversations",
            params={
                "business_id": f"eq.{self.business_id}",
                "status": f"eq.{ConversationStatus.OPEN.value}",
                "last_message_at": f"lt.{before.isoformat()}",
                "select": "id",
            },
        )
        for row in rows:
            await self.update_conversation(row["id"], status=ConversationStatus.CLOSED.value)
        return len(rows)

    async def last_10_calls_stats(self) -> dict:
        rows = await self._request(
            "GET", "missed_calls",
            params={
                "business_id": f"eq.{self.business_id}",
                "select": "text_sent,duplicate_suppressed,created_at",
                "order": "created_at.desc",
                "limit": "10",
            },
        )
        return {
            "count": len(rows),
            "texts_sent": sum(1 for row in rows if row.get("text_sent")),
            "duplicate_suppressed": sum(1 for row in rows if row.get("duplicate_suppressed")),
        }

    async def demo_snapshot(self) -> dict:
        calls = await self._request(
            "GET", "missed_calls",
            params={
                "business_id": f"eq.{self.business_id}",
                "select": "from_number,text_sent,duplicate_suppressed,created_at",
                "order": "created_at.desc",
                "limit": "5",
            },
        )
        conversations = await self._request(
            "GET", "conversations",
            params={
                "business_id": f"eq.{self.business_id}",
                "select": "phone_number,status,lead_extracted,last_message_at,messages",
                "order": "last_message_at.desc",
                "limit": "5",
            },
        )
        leads = await self._request(
            "GET", "leads",
            params={
                "business_id": f"eq.{self.business_id}",
                "select": "phone_number,service_type,urgency_level,created_at",
                "order": "created_at.desc",
                "limit": "5",
            },
        )
        return {
            "tables": {
                "missed_calls": {
                    "sample": [
                        {
                            "phone": _mask_phone(row.get("from_number")),
                            "text_sent": bool(row.get("text_sent")),
                            "duplicate_suppressed": bool(row.get("duplicate_suppressed")),
                            "created_at": row.get("created_at"),
                        }
                        for row in calls
                    ],
                },
                "conversations": {
                    "sample": [
                        {
                            "phone": _mask_phone(row.get("phone_number")),
                            "status": row.get("status"),
                            "lead_extracted": bool(row.get("lead_extracted")),
                            "message_count": len(row.get("messages") or []),
                            "last_message_at": row.get("last_message_at"),
                        }
                        for row in conversations
                    ],
                },
                "leads": {
                    "sample": [
                        {
                            "phone": _mask_phone(row.get("phone_number")),
                            "service_type": row.get("service_type"),
                            "urgency_level": row.get("urgency_level"),
                            "created_at": row.get("created_at"),
                        }
                        for row in leads
                    ],
                },
            }
        }

    async def health_check(self) -> dict:
        try:
            await self._request("GET", "missed_calls", params={"select": "id", "limit": "1"})
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


supabase_client = SupabaseClient()
