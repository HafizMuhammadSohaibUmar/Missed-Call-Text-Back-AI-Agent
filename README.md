# LeadPilot AI Missed Call Text-Back Agent

AI-powered missed-call recovery for home-service businesses.

This service listens for Twilio call-status webhooks, sends a fast missed-call SMS when a call is not answered or busy, manages the SMS conversation, qualifies the lead, alerts the owner, and stores the full thread in Supabase.

## Related AI Systems

| System | Purpose | Live Demo | Repository |
| --- | --- | --- | --- |
| LeadPilot AI Voice Agent | Inbound phone agent for call qualification, emergency detection, and lead logging. | [Live Demo](https://leadpilotai.sohaib.systems/) | [Repository](https://github.com/HafizMuhammadSohaibUmar/LeadPilotAI) |
| Missed Call Text-Back AI Agent | SMS recovery and qualification after no-answer or busy calls. | [Live Demo](https://missed-call-text-back-ai-agent.sohaib.systems/demo) | **This repo** |
| Outbound Follow-Up AI Agent | Estimate, no-show, re-engagement, and seasonal follow-up campaigns. | [Live Demo](https://outbound-followup-ai-agent.sohaib.systems/demo) | [Repository](https://github.com/HafizMuhammadSohaibUmar/Outbound-Follow-Up-AI-Agent) |
| AI Auto Review Request Agent | Sentiment-aware post-job review and private feedback routing. | [Live Demo](https://ai-review-agent.sohaib.systems/demo) | [Repository](https://github.com/HafizMuhammadSohaibUmar/AI-Auto-Review-Request-Agent) |
| Web Chat Lead Qualifier Agent | Embeddable RAG chat widget for contractor websites. | [Live Demo](https://web-chat-lead-qualifier-agent.sohaib.systems/demo) | [Repository](https://github.com/HafizMuhammadSohaibUmar/Web-Chat-Lead-Qualifier-Agent) |
| Personal AI Agent | Self-hosted task, planning, and local-calendar assistant with LangGraph tools. | [Live Demo](https://personal-ai-agent.sohaib.systems/) | [Repository](https://github.com/HafizMuhammadSohaibUmar/Personal-AI-Agent) |
| Invoxia AI for ERPNext | Frappe/ERPNext assistant layer for navigation, voice input foundations, and live ERP answers. | [Live Demo](https://invoxia.sohaib.systems/) | [Repository](https://github.com/HafizMuhammadSohaibUmar/InvoxiaAI-ERPNext) |

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

## Engineering Points

- Twilio call-status and SMS webhooks are handled as separate but connected workflows.
- STOP/UNSUBSCRIBE handling is checked before any AI generation or outbound message.
- Duplicate and rate-limit checks prevent repeatedly texting the same caller.
- Conversation state is persisted so qualification can happen across multiple replies.
- The browser demo exercises missed-call recovery, partial replies, lead creation, owner alert previews, and opt-out behavior without sending live SMS.

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

## Twilio Configuration

Configure the Twilio phone number webhooks:

```text
Call status callback: https://<your-domain>/twilio/call-status
Incoming message webhook: https://<your-domain>/twilio/sms-reply
```


For demo, open:

```text
https://missed-call-text-back-ai-agent.sohaib.systems/demo
```

The browser demo is dry-run only. It shows missed-call SMS previews, incomplete intake replies, qualified lead owner alerts, customer confirmations, and STOP opt-out behavior without sending real SMS.

