"""Missed-call SMS generation."""
from config import get_settings
from services.llm import completion_with_fallback
from utils import time_of_day


STYLE_BY_TIME = {
    "morning": "professional, energetic, and prompt",
    "afternoon": "direct, helpful, and efficient",
    "evening": "reassuring and calm",
    "after_hours": "apologetic for after-hours timing and promising a morning callback",
}


def fallback_missed_call_sms(period: str) -> str:
    settings = get_settings()
    if period == "after_hours":
        return (
            f"Hi, this is {settings.owner_first_name} with {settings.business_name}. "
            f"Sorry we missed your call after hours. Reply with what you need help with, "
            f"and we will follow up first thing in the morning."
        )
    return (
        f"Hi, this is {settings.owner_first_name} with {settings.business_name}. "
        f"Sorry we missed your call. Reply with what {settings.business_type} help you need, "
        f"and we will get you taken care of."
    )


async def generate_missed_call_sms() -> str:
    settings = get_settings()
    period = time_of_day()
    prompt = (
        "Write one concise SMS under 320 characters for a home-service business that missed a call. "
        f"Tone: {STYLE_BY_TIME[period]}. Variables: business_name={settings.business_name}, "
        f"business_type={settings.business_type}, owner_first_name={settings.owner_first_name}. "
        "Ask the customer to reply with what they need. Do not mention AI. Return only the SMS."
    )
    try:
        message = await completion_with_fallback([{"role": "user", "content": prompt}], max_tokens=120)
        return message[:320] if message else fallback_missed_call_sms(period)
    except Exception:
        return fallback_missed_call_sms(period)
