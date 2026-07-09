"""LiteLLM helpers with retry and fallback."""
import asyncio
import os
from typing import Any

import litellm

from config import get_settings

litellm.suppress_debug_info = True


async def completion_with_fallback(messages: list[dict[str, str]], *, max_tokens: int = 200,
                                   temperature: float = 0.2) -> str:
    settings = get_settings()
    if settings.mistral_api_key:
        os.environ["MISTRAL_API_KEY"] = settings.mistral_api_key
    models = [settings.primary_model, settings.fallback_model]
    last_error: Exception | None = None
    for index, model in enumerate(models):
        for attempt in range(2):
            try:
                response: Any = await asyncio.wait_for(
                    litellm.acompletion(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        timeout=settings.llm_timeout_seconds,
                    ),
                    timeout=settings.llm_timeout_seconds + 1,
                )
                return (response.choices[0].message.content or "").strip()
            except Exception as exc:
                last_error = exc
                await asyncio.sleep(0.25 * (2 ** attempt) * (index + 1))
    raise RuntimeError(f"LLM failed after fallback: {last_error}")
