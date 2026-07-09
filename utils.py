"""Small shared utilities."""
import re
from datetime import datetime
from zoneinfo import ZoneInfo

STOP_WORDS = {"STOP", "UNSUBSCRIBE", "CANCEL", "QUIT", "END", "OPTOUT", "OPT OUT"}


def normalize_phone(raw: str, default_country_code: str = "+1") -> str:
    raw = (raw or "").strip()
    if raw.startswith("+"):
        return "+" + re.sub(r"\D", "", raw)
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"{default_country_code}{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    if digits:
        return f"+{digits}"
    return raw


def is_stop_message(body: str) -> bool:
    return (body or "").strip().upper() in STOP_WORDS


def time_of_day(now: datetime | None = None, timezone_name: str = "UTC") -> str:
    current = now or datetime.now(ZoneInfo(timezone_name))
    hour = current.hour
    if 8 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 20:
        return "evening"
    return "after_hours"
