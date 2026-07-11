# LeadPilot AI Missed Call Text-Back Agent

AI-powered missed-call recovery for home-service businesses.

This service listens for Twilio call-status webhooks, sends a fast missed-call SMS when a call is not answered or busy, manages the SMS conversation, qualifies the lead, alerts the owner, and stores the full thread in Supabase.

## Related AI Systems

| System | Purpose | Links |
| --- | --- | --- |
| LeadPilot AI Voice Agent | Inbound phone agent for call qualification, emergency detection, and lead logging. | [Live](https://leadpilotai.sohaib.systems/) · [Repo](https://github.com/HafizMuhammadSohaibUmar/LeadPilotAI) |
| Missed Call Text-Back AI Agent | SMS recovery and qualification after no-answer or busy calls. | [Live](https://missed-call-text-back-ai-agent.sohaib.systems/demo) · [Repo](https://github.com/HafizMuhammadSohaibUmar/Missed-Call-Text-Back-AI-Agent) |
| Outbound Follow-Up AI Agent | Estimate, no-show, re-engagement, and seasonal follow-up campaigns. | [Live](https://outbound-followup-ai-agent.sohaib.systems/demo) · [Repo](https://github.com/HafizMuhammadSohaibUmar/Outbound-Follow-Up-AI-Agent) |
| AI Auto Review Request Agent | Sentiment-aware post-job review and private feedback routing. | [Live](https://ai-review-agent.sohaib.systems/demo) · [Repo](https://github.com/HafizMuhammadSohaibUmar/AI-Auto-Review-Request-Agent) |
| Web Chat Lead Qualifier Agent | Embeddable RAG chat widget for contractor websites. | [Live](https://web-chat-lead-qualifier-agent.sohaib.systems/demo) · [Repo](https://github.com/HafizMuhammadSohaibUmar/Web-Chat-Lead-Qualifier-Agent) |
| Personal AI Agent | Local task, planning, and calendar assistant with LangGraph tools. | [Live](https://personal-ai-agent.sohaib.systems/) · [Repo](https://github.com/HafizMuhammadSohaibUmar/Personal-AI-Agent) |
| Invoxia AI for ERPNext | Frappe/ERPNext assistant layer for navigation, voice input foundations, and live ERP answers. | [Live](https://invoxia.sohaib.systems/) · [Repo](https://github.com/HafizMuhammadSohaibUmar/InvoxiaAI-ERPNext) |

## Architecture

```text
Twilio Call Status Webhook
  -> FastAPI /twilio/call-status
  -> Twilio signature validation
  -> E.164 phone normalization
  -> suppression + duplicate + rate-limit checks
  -> LiteLLM/Mistral missed-call SMS generation
  -> Twilio SMS or dry-run preview
  -> Supabase missed_calls + conversations

Customer SMS Reply
  -> FastAPI /twilio/sms-reply
  -> STOP suppression or conversation state load
  -> LiteLLM qualification over last 10 messages
  -> lead creation + owner SMS + customer confirmation
```

## What It Proves

- Fast webhook-to-SMS recovery for missed inbound demand.
- Consent-aware SMS handling with STOP suppression before any AI call.
- Conversation memory with lead extraction rather than one-off text generation.
- Safe public demo mode that previews the exact messages without sending SMS.
- Multi-tenant data shape through `business_id`.

## Core Flow

1. Twilio sends `CallStatus=no-answer` or `CallStatus=busy` to `/twilio/call-status`.
2. The webhook signature is validated.
3. The caller phone is normalized to E.164.
4. Suppressed numbers are skipped.
5. Duplicate missed-call texts within 4 hours are skipped.
6. The SMS rate limit is enforced.
7. Mistral generates a time-of-day-aware missed-call text.
8. Twilio sends the SMS.
9. Supabase stores the missed call and conversation thread.
10. Replies continue at `/twilio/sms-reply` until the lead is qualified or closed.

## Routes

| Route | Purpose |
| --- | --- |
| `POST /twilio/call-status` | Twilio call status webhook for missed calls |
| `POST /twilio/sms-reply` | Twilio inbound SMS webhook |
| `GET /demo` | Browser demo for missed-call and reply scenarios |
| `POST /demo/missed-call` | Dry-run missed-call demo trigger |
| `POST /demo/reply` | Dry-run reply/qualification demo trigger |
| `GET /health` | Supabase, Twilio, and last-10-calls stats |
| `GET /docs` | FastAPI OpenAPI docs |

## AI Behavior

The missed-call SMS uses time-of-day tone:

- 8am-12pm: professional and energetic
- 12pm-5pm: direct and efficient
- 5pm-8pm: reassuring
- 8pm-8am: apologetic after-hours message with a morning callback promise

Conversation replies load the last 10 messages and extract:

- name
- service type
- address
- urgency level

When complete, the system creates a lead, notifies the owner, confirms with the customer, and closes the conversation as qualified.

## Local Setup

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn main:app --port 8002
```

Run the Supabase migration:

```text
db/migrations/001_init.sql
```

## Testing

```bash
pytest tests/ -v
```

## Deployment

This service can run on the same DigitalOcean Droplet and Supabase project as the other LeadPilot AI agents.

Suggested port:

```text
8002
```

Suggested Caddy route:

```caddy
missed-calls.yourdomain.com {
    reverse_proxy 127.0.0.1:8002
}
```

Then set:

```env
PUBLIC_BASE_URL=https://missed-calls.yourdomain.com
```

## Twilio Configuration

Configure the Twilio phone number webhooks:

```text
Call status callback: https://missed-calls.yourdomain.com/twilio/call-status
Incoming message webhook: https://missed-calls.yourdomain.com/twilio/sms-reply
```

For portfolio demos and Twilio trial accounts:

```env
SMS_DRY_RUN=true
DEMO_MODE_ENABLED=true
```

Then open:

```text
https://missed-call-text-back-ai-agent.sohaib.systems/demo
```

The browser demo is dry-run only. It shows missed-call SMS previews, incomplete intake replies, qualified lead owner alerts, customer confirmations, and STOP opt-out behavior without sending real SMS.
