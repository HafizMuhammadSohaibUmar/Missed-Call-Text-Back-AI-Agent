"""AI qualification and deterministic fallback extraction."""
import json
import re
from typing import Any

from models.lead import UrgencyLevel
from services.llm import completion_with_fallback


REQUIRED_FIELDS = ("name", "service_type", "address", "urgency_level")


def _fallback_extract(transcript: str) -> dict[str, Any]:
    lower = transcript.lower()
    urgency = UrgencyLevel.UNKNOWN
    if any(word in lower for word in ["emergency", "flood", "leak", "no heat", "no ac", "sparking"]):
        urgency = UrgencyLevel.EMERGENCY
    elif any(word in lower for word in ["today", "asap", "same day", "urgent"]):
        urgency = UrgencyLevel.SAME_DAY
    address_match = re.search(r"\d{2,6}\s+[A-Za-z0-9 .'-]+", transcript)
    return {
        "complete": False,
        "name": "",
        "service_type": "",
        "address": address_match.group(0).strip() if address_match else "",
        "urgency_level": urgency.value,
        "reply": "Thanks. What is your name, service address, and what service do you need help with?",
    }


async def qualify(messages: list[dict[str, Any]]) -> dict[str, Any]:
    transcript = "\n".join(f"{m.get('role')}: {m.get('body')}" for m in messages[-10:])
    prompt = (
        "You are a home-service intake agent. From this SMS conversation, extract JSON only with: "
        "complete(boolean), name, service_type, address, urgency_level(one of emergency,same_day,soon,flexible,unknown), reply. "
        "If any required field is missing, complete=false and reply should ask for only the missing fields. "
        "If complete=true, reply should be a short confirmation. Conversation:\n"
        f"{transcript}"
    )
    try:
        raw = await completion_with_fallback([{"role": "user", "content": prompt}], max_tokens=300)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        parsed = json.loads(raw[start:end])
        for field in REQUIRED_FIELDS:
            parsed.setdefault(field, "")
        parsed.setdefault("complete", False)
        parsed.setdefault("reply", "Thanks. What service do you need help with?")
        if parsed.get("urgency_level") not in {u.value for u in UrgencyLevel}:
            parsed["urgency_level"] = UrgencyLevel.UNKNOWN.value
        return parsed
    except Exception:
        return _fallback_extract(transcript)
