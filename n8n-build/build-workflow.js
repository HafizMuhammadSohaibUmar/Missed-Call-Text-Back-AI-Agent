const fs = require('node:fs');
const path = require('node:path');
const out = __dirname;
const expr = (s) => `={{ ${s} }}`;
const body = (fn) => fn.toString().slice(fn.toString().indexOf('{') + 1, -1).trim();
const node = (name, type, typeVersion, parameters, x, y, extra = {}) => ({ id: name.toLowerCase().replace(/[^a-z0-9]+/g, '-'), name, type, typeVersion, parameters, position: [x, y], ...extra });
const base = (name, type, version, params, x, y, extra) => node(name, `n8n-nodes-base.${type}`, version, params, x, y, extra);
const lang = (name, type, version, params, x, y, extra) => node(name, `@n8n/n8n-nodes-langchain.${type}`, version, params, x, y, extra);
const link = (name, type = 'main', index = 0) => ({ node: name, type, index });

function normalizeMissedCall() {
  const p = $input.first().json.body ?? $input.first().json;
  const status = String(p.CallStatus ?? p.call_status ?? '').toLowerCase();
  if (!['no-answer', 'busy'].includes(status)) return [];
  if (!p.From || !p.To || !p.CallSid) throw new Error('Twilio From, To, and CallSid are required');
  return [{ json: { phone: p.From, business_phone: p.To, call_sid: p.CallSid, call_status: status, received_at: new Date().toISOString() } }];
}

function duplicateDecision() {
  const call = $('Normalize Missed Call').first().json;
  const cutoff = Date.now() - 4 * 60 * 60 * 1000;
  const rows = $input.all().map(i => i.json).filter(r => r.from_number);
  return [{ json: { ...call, duplicate: rows.some(r => r.call_sid === call.call_sid || (r.from_number === call.phone && Date.parse(r.created_at) >= cutoff)) } }];
}

function normalizeReply() {
  const p = $input.first().json.body ?? $input.first().json;
  if (!p.From || !p.Body || !p.MessageSid) throw new Error('Twilio From, Body, and MessageSid are required');
  const text = String(p.Body).trim();
  const stop = /^(stop|unsubscribe|cancel|quit|end|opt\s*out)$/i.test(text);
  return [{ json: { phone: p.From, business_phone: p.To, message: text, message_sid: p.MessageSid, stop } }];
}

function parseQualification() {
  const raw = String($input.first().json.output ?? $input.first().json.text ?? '');
  const cleaned = raw.replace(/^```(?:json)?/i, '').replace(/```$/i, '').trim();
  let q;
  try { q = JSON.parse(cleaned); } catch { throw new Error(`AI response was not valid JSON: ${raw.slice(0, 240)}`); }
  const required = ['name', 'service_type', 'address', 'urgency_level'];
  q.complete = required.every(k => typeof q[k] === 'string' && q[k].trim());
  if (!q.reply) throw new Error('AI response omitted reply');
  return [{ json: { ...$('Normalize SMS Reply').first().json, ...q } }];
}

const aiSystem = `You are the SMS intake assistant for REPLACE_WITH_BUSINESS_NAME, a home-service business.
Return JSON only with keys: complete, name, service_type, address, urgency_level, reply.
Required qualification fields are name, service_type, address, and urgency_level. urgency_level must be emergency, same_day, soon, flexible, or unknown.
Ask for only missing fields, in one concise SMS under 320 characters. Never invent details, prices, availability, or appointments.
If there is fire, smoke, gas odor, active sparking, immediate danger, or a medical emergency, tell the customer to contact emergency services or the utility first; never claim dispatch.
When all fields are present, set complete=true and say a team member will follow up; do not say an appointment is booked.
STOP handling occurs before this agent and must never be delegated to the model.`;

const workflow = {
  id: 'MissedCallN8n20261010', name: 'Missed Call Text-Back - n8n Only (inactive until configured)', active: false,
  settings: { executionOrder: 'v1', timezone: 'America/New_York', errorWorkflow: '' }, staticData: null,
  nodes: [
    base('Credential and Safety Notes', 'stickyNote', 1, { width: 720, height: 440, content:
      '## Credentials required before activation\n1. Twilio: Account SID, Auth Token, approved SMS sender, call-status webhook, inbound-message webhook.\n2. Supabase: project URL and service-role credential for the three tables in schema.sql.\n3. LiteLLM/OpenAI-compatible credential: base URL plus API key, configured on both Mistral Chat Model nodes; model alias must resolve to Mistral.\n4. Jobber OAuth2 OR Housecall Pro API credential; configure only the selected CRM branch.\n5. Owner E.164 phone number.\n\nImport note: valid JSON cannot contain comments, so this sticky note is the requested top-of-file credential block. Keep inactive until Twilio signature validation, consent, sender registration, STOP handling, duplicate protection, CRM sandbox creation, and internal-number testing pass. Replace every REPLACE_WITH_* value.' }, -520, -620),

    base('Twilio Call Status Webhook', 'webhook', 1, { httpMethod: 'POST', path: 'missed-call-status-n8n', responseMode: 'onReceived', options: {} }, -380, -180),
    base('Normalize Missed Call', 'code', 2, { jsCode: body(normalizeMissedCall) }, -160, -180),
    base('Recent Missed Calls (Supabase)', 'supabase', 1, { resource: 'row', operation: 'getAll', tableId: 'n8n_missed_calls', returnAll: true, filters: { conditions: [{ keyName: 'from_number', condition: 'eq', keyValue: expr("$('Normalize Missed Call').first().json.phone") }, { keyName: 'created_at', condition: 'gte', keyValue: expr('$now.minus({ hours: 4 }).toISO()') }] }, options: {} }, 60, -180, { alwaysOutputData: true }),
    base('Four-Hour Duplicate Check', 'code', 2, { jsCode: body(duplicateDecision) }, 280, -180),
    base('New Missed Call?', 'if', 2, { conditions: { options: { typeValidation: 'strict' }, conditions: [{ leftValue: expr('$json.duplicate'), rightValue: false, operator: { type: 'boolean', operation: 'equal' } }] }, options: {} }, 500, -180),
    lang('Initial Text Personalizer', 'agent', 2.2, { promptType: 'define', text: expr("'Create the initial missed-call text for phone ' + $json.phone + '. Current local time: ' + $now.setZone('America/New_York').toFormat('cccc, h:mm a') + '. Return only the SMS text.'"), options: { systemMessage: 'Write one warm missed-call SMS under 320 characters for REPLACE_WITH_BUSINESS_NAME. Identify the business, apologize for missing the call, adjust naturally for morning/afternoon/evening/after-hours, and ask what service help they need. Do not mention AI. Do not promise same-day service. End with: Reply STOP to opt out.' } }, 740, -180),
    lang('Mistral Model - Initial', 'lmChatOpenAi', 1.2, { modelName: 'REPLACE_WITH_LITELLM_MISTRAL_MODEL', options: { baseURL: 'REPLACE_WITH_LITELLM_OPENAI_BASE_URL' } }, 720, 20),
    lang('Phone Memory - Initial', 'memoryBufferWindow', 1.3, { sessionKey: expr("$('Normalize Missed Call').first().json.phone"), contextWindowLength: 10 }, 920, 20),
    base('Send Initial SMS', 'twilio', 1, { resource: 'sms', operation: 'send', from: 'REPLACE_WITH_TWILIO_E164', to: expr("$('Normalize Missed Call').first().json.phone"), message: expr('$json.output') }, 980, -180),
    base('Log Missed Call', 'supabase', 1, { resource: 'row', operation: 'create', tableId: 'n8n_missed_calls', dataToSend: 'defineBelow', fieldsUi: { fieldValues: [['call_sid', expr("$('Normalize Missed Call').first().json.call_sid")], ['from_number', expr("$('Normalize Missed Call').first().json.phone")], ['to_number', expr("$('Normalize Missed Call').first().json.business_phone")], ['call_status', expr("$('Normalize Missed Call').first().json.call_status")], ['text_sent', true]].map(([fieldId, fieldValue]) => ({ fieldId, fieldValue })) } }, 1200, -180),

    base('Twilio SMS Reply Webhook', 'webhook', 1, { httpMethod: 'POST', path: 'missed-call-reply-n8n', responseMode: 'onReceived', options: {} }, -380, 300),
    base('Normalize SMS Reply', 'code', 2, { jsCode: body(normalizeReply) }, -160, 300),
    base('STOP Word?', 'if', 2, { conditions: { options: { typeValidation: 'strict' }, conditions: [{ leftValue: expr('$json.stop'), rightValue: true, operator: { type: 'boolean', operation: 'equal' } }] }, options: {} }, 60, 300),
    base('Upsert Suppression', 'supabase', 1, { resource: 'row', operation: 'upsert', tableId: 'n8n_sms_suppression', dataToSend: 'defineBelow', fieldsUi: { fieldValues: [['phone_number', expr('$json.phone')], ['reason', 'STOP'], ['source_message_sid', expr('$json.message_sid')]].map(([fieldId, fieldValue]) => ({ fieldId, fieldValue })) } }, 300, 160),
    base('Confirm Opt-Out Once', 'twilio', 1, { resource: 'sms', operation: 'send', from: 'REPLACE_WITH_TWILIO_E164', to: expr("$('Normalize SMS Reply').first().json.phone"), message: 'You have been unsubscribed and will receive no further messages from REPLACE_WITH_BUSINESS_NAME.' }, 540, 160),
    base('Check Existing Suppression', 'supabase', 1, { resource: 'row', operation: 'getAll', tableId: 'n8n_sms_suppression', returnAll: true, filters: { conditions: [{ keyName: 'phone_number', condition: 'eq', keyValue: expr('$json.phone') }] }, options: {} }, 300, 420, { alwaysOutputData: true }),
    base('Is Already Suppressed?', 'if', 2, { conditions: { options: { typeValidation: 'loose' }, conditions: [{ leftValue: expr('$json.phone_number'), rightValue: '', operator: { type: 'string', operation: 'notEmpty' } }] }, options: {} }, 540, 420),
    lang('Qualification AI Agent', 'agent', 2.2, { promptType: 'define', text: expr("$('Normalize SMS Reply').first().json.message"), options: { systemMessage: aiSystem } }, 780, 500),
    lang('Mistral Model - Qualification', 'lmChatOpenAi', 1.2, { modelName: 'REPLACE_WITH_LITELLM_MISTRAL_MODEL', options: { baseURL: 'REPLACE_WITH_LITELLM_OPENAI_BASE_URL', responseFormat: 'json_object' } }, 760, 700),
    lang('Phone Memory - Replies', 'memoryBufferWindow', 1.3, { sessionKey: expr("$('Normalize SMS Reply').first().json.phone"), contextWindowLength: 10 }, 980, 700),
    base('Parse Qualification JSON', 'code', 2, { jsCode: body(parseQualification) }, 1020, 500),
    base('Send AI Reply', 'twilio', 1, { resource: 'sms', operation: 'send', from: 'REPLACE_WITH_TWILIO_E164', to: expr('$json.phone'), message: expr('$json.reply') }, 1240, 500),
    base('Qualification Complete?', 'if', 2, { conditions: { options: { typeValidation: 'strict' }, conditions: [{ leftValue: expr('$json.complete'), rightValue: true, operator: { type: 'boolean', operation: 'equal' } }] }, options: {} }, 1460, 500),
    base('CRM Provider', 'switch', 3, { mode: 'expression', numberOutputs: 2, output: expr("'REPLACE_WITH_CRM_PROVIDER' === 'jobber' ? 0 : 1"), options: {} }, 1680, 500),
    base('Create Jobber Request', 'httpRequest', 4.2, { method: 'POST', url: 'https://api.getjobber.com/api/graphql', authentication: 'genericCredentialType', genericAuthType: 'oAuth2Api', sendHeaders: true, headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }, { name: 'X-JOBBER-GRAPHQL-VERSION', value: 'REPLACE_WITH_SUPPORTED_JOBBER_VERSION' }] }, sendBody: true, specifyBody: 'json', jsonBody: expr("JSON.stringify({query:'mutation CreateRequest($input: RequestCreateInput!) { requestCreate(input: $input) { request { id } userErrors { message } } }',variables:{input:{title:$json.service_type,instructions:'Missed-call lead: '+$json.name+' | '+$json.phone+' | '+$json.address+' | Urgency: '+$json.urgency_level}}})"), options: { timeout: 15000 } }, 1920, 400),
    base('Create Housecall Pro Lead', 'httpRequest', 4.2, { method: 'POST', url: 'REPLACE_WITH_HOUSECALL_PRO_LEAD_ENDPOINT', authentication: 'genericCredentialType', genericAuthType: 'httpHeaderAuth', sendBody: true, specifyBody: 'json', jsonBody: expr("JSON.stringify({name:$json.name,phone:$json.phone,address:$json.address,service_type:$json.service_type,urgency:$json.urgency_level,source:'missed_call_text_back'})"), options: { timeout: 15000 } }, 1920, 620),
    base('Notify Owner', 'twilio', 1, { resource: 'sms', operation: 'send', from: 'REPLACE_WITH_TWILIO_E164', to: 'REPLACE_WITH_OWNER_E164', message: expr("'Qualified missed-call lead: ' + $('Parse Qualification JSON').first().json.name + ', ' + $('Parse Qualification JSON').first().json.phone + ', ' + $('Parse Qualification JSON').first().json.service_type + ', ' + $('Parse Qualification JSON').first().json.address + ', urgency: ' + $('Parse Qualification JSON').first().json.urgency_level") }, 2160, 500),
    base('Log Qualified Lead', 'supabase', 1, { resource: 'row', operation: 'create', tableId: 'n8n_missed_call_leads', dataToSend: 'defineBelow', fieldsUi: { fieldValues: [['phone_number', expr("$('Parse Qualification JSON').first().json.phone")], ['name', expr("$('Parse Qualification JSON').first().json.name")], ['service_type', expr("$('Parse Qualification JSON').first().json.service_type")], ['address', expr("$('Parse Qualification JSON').first().json.address")], ['urgency_level', expr("$('Parse Qualification JSON').first().json.urgency_level")]].map(([fieldId, fieldValue]) => ({ fieldId, fieldValue })) } }, 2400, 500),
  ],
  connections: {
    'Twilio Call Status Webhook': { main: [[link('Normalize Missed Call')]] }, 'Normalize Missed Call': { main: [[link('Recent Missed Calls (Supabase)')]] },
    'Recent Missed Calls (Supabase)': { main: [[link('Four-Hour Duplicate Check')]] }, 'Four-Hour Duplicate Check': { main: [[link('New Missed Call?')]] },
    'New Missed Call?': { main: [[link('Initial Text Personalizer')], []] }, 'Initial Text Personalizer': { main: [[link('Send Initial SMS')]] },
    'Mistral Model - Initial': { ai_languageModel: [[link('Initial Text Personalizer', 'ai_languageModel')]] }, 'Phone Memory - Initial': { ai_memory: [[link('Initial Text Personalizer', 'ai_memory')]] },
    'Send Initial SMS': { main: [[link('Log Missed Call')]] },
    'Twilio SMS Reply Webhook': { main: [[link('Normalize SMS Reply')]] }, 'Normalize SMS Reply': { main: [[link('STOP Word?')]] },
    'STOP Word?': { main: [[link('Upsert Suppression')], [link('Check Existing Suppression')]] }, 'Upsert Suppression': { main: [[link('Confirm Opt-Out Once')]] },
    'Check Existing Suppression': { main: [[link('Is Already Suppressed?')]] }, 'Is Already Suppressed?': { main: [[], [link('Qualification AI Agent')]] },
    'Mistral Model - Qualification': { ai_languageModel: [[link('Qualification AI Agent', 'ai_languageModel')]] }, 'Phone Memory - Replies': { ai_memory: [[link('Qualification AI Agent', 'ai_memory')]] },
    'Qualification AI Agent': { main: [[link('Parse Qualification JSON')]] }, 'Parse Qualification JSON': { main: [[link('Send AI Reply')]] },
    'Send AI Reply': { main: [[link('Qualification Complete?')]] }, 'Qualification Complete?': { main: [[link('CRM Provider')], []] },
    'CRM Provider': { main: [[link('Create Jobber Request')], [link('Create Housecall Pro Lead')]] },
    'Create Jobber Request': { main: [[link('Notify Owner')]] }, 'Create Housecall Pro Lead': { main: [[link('Notify Owner')]] }, 'Notify Owner': { main: [[link('Log Qualified Lead')]] },
  },
};

fs.writeFileSync(path.join(out, 'missed-call-text-back-n8n.json'), JSON.stringify(workflow, null, 2) + '\n');
