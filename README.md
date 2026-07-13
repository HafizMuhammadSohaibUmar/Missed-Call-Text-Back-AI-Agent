# LeadPilot AI Missed Call Text-Back Agent

AI-powered missed-call recovery and SMS lead qualification for home-service businesses.

The agent listens for Twilio call-status webhooks, identifies no-answer or busy calls, sends a fast personalized SMS, manages the reply conversation, extracts lead details, handles opt-outs, alerts the owner, and stores the full workflow in Supabase.

## Live Demo

- Live demo: `https://missed-call-text-back-ai-agent.sohaib.systems/demo`
- Health check: `https://missed-call-text-back-ai-agent.sohaib.systems/health`
- Repository: `https://github.com/HafizMuhammadSohaibUmar/Missed-Call-Text-Back-AI-Agent`

How to evaluate the demo:

1. Simulate a missed call with `No answer` or `Busy`.
2. Review the generated missed-call SMS preview.
3. Try a complete reply, a missing-address reply, and a STOP reply.
4. Confirm the output changes between AI intake, owner alert, customer confirmation, and opt-out handling.
5. Check the safe database preview for masked recent activity.

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

## What This Agent Does

- Receives Twilio call-status webhooks.
- Responds only to `no-answer` and `busy` calls.
- Validates Twilio webhook signatures.
- Normalizes caller numbers to E.164.
- Checks STOP suppressions before sending anything.
- Suppresses duplicate missed-call texts within a 4-hour window.
- Enforces a maximum of 3 texts per number per 4 hours.
- Generates time-of-day-aware missed-call SMS copy.
- Stores missed-call and conversation state in Supabase.
- Handles SMS replies through a separate Twilio webhook.
- Loads recent conversation history for lead qualification.
- Extracts name, service type, address, and urgency.
- Creates a lead, notifies the owner, and confirms with the customer.
- Handles STOP, UNSUBSCRIBE, CANCEL, QUIT, END, and OPTOUT replies.

## Architecture

```text
Twilio Call Status
  |
  | POST /twilio/call-status
  v
FastAPI missed-call handler
  |
  +--> Twilio signature validation
  +--> phone normalization
  +--> suppression, duplicate, and rate-limit checks
  +--> LiteLLM: Mistral primary, Ministral fallback
  +--> Twilio SMS or dry-run preview
  +--> Supabase: missed_calls + conversations

Customer SMS Reply
  |
  | POST /twilio/sms-reply
  v
FastAPI reply handler
  |
  +--> MessageSid deduplication
  +--> STOP suppression
  +--> conversation history
  +--> AI qualification
  +--> lead creation + owner alert + customer confirmation
```

## Conversation Flow

1. A call is missed or busy.
2. The caller is checked against suppression, duplicate, and rate-limit rules.
3. The agent sends a personalized text-back message.
4. The customer replies with their service need.
5. The agent asks only for missing qualification fields.
6. When complete, a lead is created and the owner is notified.
7. The customer receives confirmation.
8. STOP-style replies are suppressed before any AI call.

## API Surface

| Route | Purpose |
| --- | --- |
| `POST /twilio/call-status` | Twilio call-status webhook for no-answer and busy calls |
| `POST /twilio/sms-reply` | Twilio inbound SMS reply webhook |
| `GET /demo` | Human-facing dry-run demo page |
| `POST /demo/missed-call` | Browser missed-call simulation |
| `POST /demo/reply` | Browser reply and qualification simulation |
| `GET /demo/snapshot` | Sanitized public activity preview |
| `GET /health` | Supabase, Twilio, and recent-call health |
| `GET /docs` | FastAPI OpenAPI docs |

## Tech Stack

- FastAPI and Uvicorn
- Twilio Call Status, SMS, and RequestValidator
- LiteLLM
- Mistral Small primary model
- Ministral fallback model
- Supabase PostgREST
- APScheduler for stale conversation cleanup
- Pydantic Settings
- Pytest and pytest-asyncio
- Docker and Docker Compose

## Production Features

- Twilio webhook signature validation
- E.164 phone normalization
- STOP suppression before AI generation
- Twilio `MessageSid` deduplication
- 4-hour duplicate text-back window
- Per-number SMS rate limit
- Multi-tenant `business_id` fields
- Conversation history stored in Supabase
- Owner alert and customer confirmation flows
- Dry-run demo path that does not send live SMS
- Health endpoint with recent missed-call stats

## Local Setup

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn main:app --port 8002
```

Expose the app for local Twilio testing:

```bash
ngrok http 8002
```

Configure Twilio:

- Call status callback: `https://your-domain/twilio/call-status`
- Incoming message webhook: `https://your-domain/twilio/sms-reply`

## Database Setup

Run the migration in Supabase SQL Editor:

```text
db/migrations/001_init.sql
```

It creates:

- `conversations`
- `suppression_list`
- `missed_calls`
- `leads`

## Important Environment Variables

```env
PUBLIC_BASE_URL=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
OWNER_PHONE_NUMBER=
MISTRAL_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
SMS_DRY_RUN=true
VALIDATE_TWILIO_SIGNATURE=true
```

## Tests

```bash
pytest tests/ -v
```

The tests cover:

- missed-call happy path
- suppressed and duplicate calls
- SMS reply qualification
- STOP handling
- browser demo behavior
- health endpoint behavior

## Deployment

```bash
docker compose up --build -d
```

Keep `SMS_DRY_RUN=true` for public browser demos. Set it to `false` only when Twilio credentials, sender compliance, and owner/customer testing controls are ready.

## Current Demo Limitations

- The browser demo previews SMS instead of sending real messages.
- Live SMS behavior depends on Twilio account configuration and regional messaging rules.
- Jobber and Housecall Pro are not required for this agent; it only needs Twilio and Supabase.
