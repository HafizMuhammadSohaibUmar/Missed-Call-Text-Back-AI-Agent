"""APScheduler setup for stale conversation cleanup."""
from datetime import datetime, timedelta, timezone

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except ImportError:
    AsyncIOScheduler = None

from config import get_settings
from db.supabase import supabase_client


class DisabledScheduler:
    running = False

    def add_job(self, *args, **kwargs) -> None:
        return None

    def start(self) -> None:
        return None

    def shutdown(self, wait: bool = False) -> None:
        return None


scheduler = AsyncIOScheduler() if AsyncIOScheduler else DisabledScheduler()


async def cleanup_conversations() -> int:
    settings = get_settings()
    before = datetime.now(timezone.utc) - timedelta(minutes=settings.conversation_timeout_minutes)
    return await supabase_client.close_timed_out_conversations(before)


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(cleanup_conversations, "interval", minutes=15,
                          id="conversation_timeout_cleanup", replace_existing=True)
        scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
