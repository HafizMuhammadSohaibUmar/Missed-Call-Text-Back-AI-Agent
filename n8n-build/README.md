# Missed-Call Text-Back: n8n-Only Version

This is a separate, client-deployable n8n implementation. It does not replace or modify the existing FastAPI agent.

## Import

Import `missed-call-text-back-n8n.json`. It intentionally imports inactive.

Run `schema.sql` first, then configure the credentials listed in the workflow's large setup note. Replace every `REPLACE_WITH_*` value before testing.

## Twilio Webhooks

- Call status callback: `POST https://YOUR_N8N_DOMAIN/webhook/missed-call-status-n8n`
- Incoming message webhook: `POST https://YOUR_N8N_DOMAIN/webhook/missed-call-reply-n8n`

Twilio must send `CallStatus`, `CallSid`, `From`, and `To` for calls, and `MessageSid`, `From`, `To`, and `Body` for replies.

## Mistral Through LiteLLM

n8n AI Agent nodes require a chat-model subnode; a normal HTTP Request node cannot connect to that model port. Configure each **Mistral Model** node using n8n's OpenAI-compatible Chat Model credential with your LiteLLM base URL and model alias. This remains zero-code and supports Mistral behind LiteLLM.

## Safety Gates

- Only `no-answer` and `busy` calls proceed.
- Duplicate text-backs are blocked for four hours.
- STOP, UNSUBSCRIBE, CANCEL, QUIT, END, OPTOUT, and OPT OUT are handled before AI.
- Existing suppressions terminate the reply branch before AI.
- Qualification requires name, service, address, and urgency.
- CRM creation runs only after qualification is complete.
- Keep inactive until Twilio signatures are verified at ingress and sandbox tests pass.

## Validate

```powershell
node build-workflow.js
node test-workflow.js
```
