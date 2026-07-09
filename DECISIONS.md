# Decisions

This service is Agent 2 in the LeadPilot AI Agent Suite: the Missed Call Text-Back Agent for home-service businesses.

## Product Boundary

The agent only handles missed calls and SMS intake. It does not answer live calls, run outbound campaigns, or request reviews. Its job is to recover demand that would otherwise be lost after `no-answer` or `busy` calls.

## Runtime

FastAPI and Uvicorn are used because Twilio webhooks are simple HTTP requests and the workflow needs low-latency responses. APScheduler handles stale conversation cleanup without adding a paid orchestration layer.

## Data Storage

The same Supabase project can be reused with separate tables:

- `conversations`
- `suppression_list`
- `missed_calls`
- `leads`

Every table includes `business_id` so the agent can support multiple businesses later without changing API contracts.

## AI Models

The primary model is `mistral/mistral-small-latest` through LiteLLM. The fallback model is configurable and defaults to `mistral/ministral-3b-latest` because the earlier `mistral/open-ministral-3b` id was observed to fail against the Mistral API. The model names stay in environment variables so deployments can change them without code edits.

## Duplicate and Rate Limits

The agent skips duplicate missed-call text-backs when the same number was texted in the last 4 hours. It also enforces a maximum text count per number per 4-hour window.

Inbound SMS replies are deduplicated by `MessageSid` stored inside the conversation message JSON.

## Suppression

STOP-style keywords are handled before any AI call. Suppressed numbers are stored in `suppression_list`, receive one opt-out confirmation, and are never texted again by the agent.

## Qualification

The conversation manager uses the last 10 messages for context and extracts name, service type, address, and urgency. Once complete, the system creates a lead, alerts the owner, confirms with the customer, and marks the conversation qualified.

## n8n Workflow

The FastAPI backend is the portfolio-grade engineering implementation. The included n8n workflow is a client-ready no-code alternative for simple deployments where a business operator prefers n8n over maintaining a custom backend.
