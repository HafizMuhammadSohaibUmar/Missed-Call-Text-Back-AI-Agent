"""LeadPilot AI Missed Call Text-Back Agent."""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response

from config import get_settings
from db.supabase import supabase_client
from handlers.missed_call import handle_missed_call
from handlers.sms_reply import handle_sms_reply
from integrations.twilio_client import twilio_client, validate_twilio_request
from logging_utils import log_event, setup_logging
from scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    start_scheduler()
    log_event(logger, "Missed call agent starting", action="startup")
    yield
    stop_scheduler()
    log_event(logger, "Missed call agent stopping", action="shutdown")


app = FastAPI(title="LeadPilot AI Missed Call Text-Back Agent", lifespan=lifespan)


@app.get("/")
async def root():
    return {
        "service": "LeadPilot AI Missed Call Text-Back Agent",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/twilio/call-status")
async def twilio_call_status(form: dict = Depends(validate_twilio_request)):
    result = await handle_missed_call(form)
    return Response(content="<Response/>", media_type="application/xml",
                    headers={"X-LeadPilot-Status": result["status"]})


@app.post("/twilio/sms-reply")
async def twilio_sms_reply(form: dict = Depends(validate_twilio_request)):
    result = await handle_sms_reply(form)
    return Response(content="<Response/>", media_type="application/xml",
                    headers={"X-LeadPilot-Status": result["status"]})


@app.get("/health")
async def health():
    db = await supabase_client.health_check()
    twilio = await twilio_client.health_check()
    stats = await supabase_client.last_10_calls_stats() if db.get("ok") else {}
    return {
        "status": "healthy" if db.get("ok") and twilio.get("ok") else "degraded",
        "business_id": get_settings().business_id,
        "database": db,
        "twilio": twilio,
        "last_10_calls": stats,
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("main:app", host=settings.host, port=settings.port)
