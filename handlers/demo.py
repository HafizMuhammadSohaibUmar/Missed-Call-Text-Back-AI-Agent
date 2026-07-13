"""Browser demo for missed-call text-back workflows."""
from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from config import get_settings
from handlers.missed_call import handle_missed_call
from handlers.sms_reply import handle_sms_reply
from models.lead import LeadRecord
from services.notifications import lead_confirmation, owner_lead_alert
from utils import normalize_phone


DEMO_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LeadPilot AI Missed Call Text-Back Agent Demo</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #F5F0E4;
      --muted: #9A9080;
      --line: rgba(255,255,255,0.08);
      --panel: #18160E;
      --soft: #0A0908;
      --accent: #4FB39F;
      --gold: #C49A1A;
      --card2: #201D12;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; background: radial-gradient(circle at top left, rgba(47,143,126,0.16), transparent 34%), var(--soft); color: var(--ink); }
    header { padding: 34px clamp(18px, 5vw, 70px); border-bottom: 1px solid var(--line); background: rgba(17,16,9,0.92); }
    h1 { margin: 0 0 8px; font-size: clamp(30px, 4vw, 54px); letter-spacing: 0; }
    p { color: var(--muted); line-height: 1.55; }
    main { display: grid; grid-template-columns: minmax(0, 1fr) minmax(320px, 0.9fr); gap: 20px; padding: 26px clamp(18px, 5vw, 70px) 46px; }
    section { background: linear-gradient(180deg, rgba(255,255,255,0.035), rgba(255,255,255,0.015)), var(--panel); border: 1px solid var(--line); border-radius: 18px; padding: 22px; }
    label { display: block; font-weight: 650; margin: 14px 0 6px; }
    input, textarea, select { width: 100%; border: 1px solid var(--line); border-radius: 8px; padding: 11px 12px; font: inherit; background: #0f0e09; color: var(--ink); }
    textarea { min-height: 96px; resize: vertical; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .actions { display: flex; align-items: center; gap: 10px; margin-top: 16px; flex-wrap: wrap; }
    button { border: 1px solid var(--line); border-radius: 8px; background: var(--card2); color: var(--ink); padding: 10px 12px; cursor: pointer; font-weight: 650; }
    button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
    .badge, .sms-label { display: inline-flex; align-items: center; border-radius: 999px; padding: 4px 9px; background: rgba(79,179,159,0.12); color: var(--accent); border: 1px solid rgba(79,179,159,0.28); font-size: 13px; font-weight: 750; }
    pre { white-space: pre-wrap; word-break: break-word; background: #0f172a; color: #e5eefb; border-radius: 8px; padding: 14px; min-height: 220px; }
    .table-wrap { overflow: auto; border: 1px solid var(--line); border-radius: 12px; margin-top: 12px; background: #111009; }
    table { width: 100%; border-collapse: collapse; min-width: 620px; table-layout: fixed; }
    th, td { text-align: left; border-bottom: 1px solid var(--line); padding: 10px 12px; font-size: 14px; vertical-align: top; word-break: break-word; }
    th { color: var(--ink); background: rgba(255,255,255,0.04); }
    td { color: var(--muted); }
    .empty { color: var(--muted); border: 1px dashed var(--line); border-radius: 12px; padding: 14px; margin-top: 10px; }
    .sms { border: 1px solid var(--line); border-radius: 12px; padding: 14px; margin-top: 12px; background: #111009; }
    .explain { margin-top: 14px; padding: 14px; border: 1px solid rgba(196,154,26,0.22); border-left: 3px solid var(--gold); border-radius: 10px; background: rgba(196,154,26,0.08); color: var(--muted); font-size: 14px; }
    .metrics { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-top:18px; max-width:1180px; }
    .metric { border:1px solid var(--line); border-radius:8px; background:rgba(255,255,255,0.035); padding:14px; }
    .metric strong { display:block; color:var(--ink); margin-bottom:6px; }
    .metric span { display:block; color:var(--muted); font-size:14px; line-height:1.5; }
    footer { border-top:1px solid var(--line); padding:24px clamp(18px,5vw,70px); color:var(--muted); background:#0A0908; }
    .footer-top { display:grid; grid-template-columns:minmax(0,1.4fr) 1fr 1fr; gap:18px; max-width:1180px; margin:0 auto 18px; }
    .footer-brand a { color:var(--ink); font-size:24px; font-weight:900; text-decoration:none; }
    .footer-brand span { color:var(--gold); }
    .footer-brand p, .footer-col a, .footer-bottom { color:var(--muted); font-size:14px; }
    .footer-col h4 { margin:0 0 8px; color:var(--ink); }
    .footer-links-list { list-style:none; padding:0; margin:0; display:grid; gap:6px; }
    .footer-links-list a { text-decoration:none; }
    .footer-bottom { max-width:1180px; margin:0 auto; display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; border-top:1px solid var(--line); padding-top:16px; }
    .footer-bottom-links { display:flex; gap:12px; flex-wrap:wrap; }
    .footer-bottom a { color:var(--ink); text-decoration:none; }
    @media (max-width: 880px) { main { grid-template-columns: 1fr; } .row, .metrics, .footer-top { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <span class="badge">Demo mode</span>
    <h1>LeadPilot AI Missed Call Text-Back Agent</h1>
    <p>Simulate a missed inbound call, generate the first response text, then continue the SMS conversation until the lead is qualified or opted out.</p>
    <div class="metrics">
      <div class="metric"><strong>Problem solved</strong><span>Home-service businesses lose urgent leads when calls are missed. The agent responds quickly and keeps the conversation moving.</span></div>
      <div class="metric"><strong>How it works</strong><span>Twilio call-status and SMS webhooks feed FastAPI handlers, Supabase stores state, and the AI intake asks only for missing fields.</span></div>
      <div class="metric"><strong>How to evaluate</strong><span>Run a missed-call event, try complete/missing/STOP replies, and check whether owner alerts, confirmations, and suppression behavior change correctly.</span></div>
    </div>
    <div class="explain">The browser demo uses the production handler path with SMS in dry-run preview mode, so no real customer is contacted.</div>
  </header>
  <main>
    <section>
      <h2>Missed Call Event</h2>
      <form id="missed-form">
        <div class="row">
          <div>
            <label for="caller_phone">Caller phone</label>
            <input id="caller_phone" name="caller_phone" required>
          </div>
          <div>
            <label for="call_status">Call status</label>
            <select id="call_status" name="call_status">
              <option value="no-answer">No answer</option>
              <option value="busy">Busy</option>
            </select>
          </div>
        </div>
        <label for="time_scenario">SMS tone</label>
        <select id="time_scenario" name="time_scenario">
          <option value="morning">Morning energetic</option>
          <option value="afternoon">Afternoon direct</option>
          <option value="evening">Evening reassuring</option>
          <option value="after_hours">After-hours apologetic</option>
        </select>
        <div class="actions">
          <button class="primary" type="submit">Simulate Missed Call</button>
          <span id="missed-status"></span>
        </div>
      </form>
      <h2>Customer Reply</h2>
      <form id="reply-form">
        <label for="reply_scenario">Reply scenario</label>
        <select id="reply_scenario" name="reply_scenario">
          <option value="complete">Complete lead</option>
          <option value="incomplete">Missing address</option>
          <option value="stop">STOP opt-out</option>
        </select>
        <label for="reply_body">Customer message</label>
        <textarea id="reply_body" name="reply_body">Hi, my name is Jane Doe. I need AC repair today at 123 Main Street.</textarea>
        <div class="actions">
          <button class="primary" type="submit">Simulate Reply</button>
          <span id="reply-status"></span>
        </div>
      </form>
    </section>
    <section>
      <h2>Agent Output</h2>
      <pre id="result">Run a missed call to start the demo.</pre>
      <div id="messages"></div>
      <h2>Safe Database Preview</h2>
      <p class="explain">Masked Supabase snapshot from the agent tables. Phone numbers and message bodies are not exposed.</p>
      <div id="snapshot">Loading sanitized table preview...</div>
    </section>
  </main>
  <footer>
    <div class="footer-top">
      <div class="footer-brand">
        <a href="https://sohaib.systems/" target="_blank" rel="noreferrer">Sohaib<span>.</span></a>
        <p>AI Solutions Engineer building practical automation systems for home-service lead capture, follow-up, and customer communication.</p>
      </div>
      <div class="footer-col">
        <h4>Project</h4>
        <ul class="footer-links-list">
          <li><a href="https://github.com/HafizMuhammadSohaibUmar/Missed-Call-Text-Back-AI-Agent" target="_blank" rel="noreferrer">GitHub Repository</a></li>
          <li><a href="/health" target="_blank" rel="noreferrer">Health Check</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Connect</h4>
        <ul class="footer-links-list">
          <li><a href="https://sohaib.systems/portfolio.html" target="_blank" rel="noreferrer">Project Portfolio</a></li>
          <li><a href="mailto:hafizmuhammadsohaibumar@gmail.com">Email</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>2026 Hafiz Muhammad Sohaib Umar</span>
      <div class="footer-bottom-links"><a href="https://sohaib.systems/" target="_blank" rel="noreferrer">sohaib.systems</a><a href="https://github.com/HafizMuhammadSohaibUmar" target="_blank" rel="noreferrer">GitHub</a></div>
    </div>
  </footer>
  <script>
    function nextDemoPhone() { return "+1555" + String(Date.now()).slice(-7); }
    const phoneInput = document.getElementById("caller_phone");
    phoneInput.value = nextDemoPhone();
    const replyBodies = {
      complete: "Hi, my name is Jane Doe. I need AC repair today at 123 Main Street.",
      incomplete: "Hi, I need help with my AC today.",
      stop: "STOP"
    };
    document.getElementById("reply_scenario").addEventListener("change", (event) => {
      document.getElementById("reply_body").value = replyBodies[event.target.value];
    });
    function render(body, ok) {
      document.getElementById("result").textContent = JSON.stringify(body, null, 2);
      document.getElementById("messages").innerHTML = (body.sms_preview || []).map((sms) =>
        `<div class="sms"><span class="sms-label">${sms.label}</span><br><strong>${sms.to}</strong><p>${sms.body}</p></div>`
      ).join("");
      return ok ? "Done" : "Failed";
    }
    async function refreshSnapshot() {
      try {
        const response = await fetch("/demo/snapshot");
        renderSnapshot(await response.json());
      } catch (error) {
        document.getElementById("snapshot").textContent = "Snapshot unavailable.";
      }
    }
    function renderSnapshot(data) {
      const root = document.getElementById("snapshot");
      const tables = data.tables || {};
      root.innerHTML = Object.entries(tables).map(([name, table]) => {
        const rows = table.sample || [];
        if (!rows.length) return `<h3>${title(name)}</h3><div class="empty">No recent demo-safe rows yet.</div>`;
        const cols = Object.keys(rows[0]);
        return `<h3>${title(name)}</h3><div class="table-wrap"><table><thead><tr>${cols.map(c => `<th>${title(c)}</th>`).join("")}</tr></thead><tbody>${rows.map(row => `<tr>${cols.map(c => `<td>${escapeHtml(String(row[c] ?? ""))}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
      }).join("");
    }
    function title(value) { return value.replaceAll("_", " ").replace(/\\b\\w/g, c => c.toUpperCase()); }
    function escapeHtml(value) {
      return value.replace(/[&<>"']/g, (ch) => {
        if (ch === "&") return "&amp;";
        if (ch === "<") return "&lt;";
        if (ch === ">") return "&gt;";
        if (ch === '"') return "&quot;";
        return "&#39;";
      });
    }
    document.getElementById("missed-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(event.target).entries());
      const response = await fetch("/demo/missed-call", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
      });
      const body = await response.json();
      document.getElementById("missed-status").textContent = render(body, response.ok);
      refreshSnapshot();
    });
    document.getElementById("reply-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(event.target).entries());
      data.caller_phone = phoneInput.value;
      const response = await fetch("/demo/reply", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
      });
      const body = await response.json();
      document.getElementById("reply-status").textContent = render(body, response.ok);
      if (data.reply_scenario === "stop" || body.result?.status === "lead_created") {
        phoneInput.value = nextDemoPhone();
      }
      refreshSnapshot();
    });
    refreshSnapshot();
  </script>
</body>
</html>"""


def sms_for_scenario(scenario: str) -> str:
    settings = get_settings()
    messages = {
        "morning": f"Hi, this is {settings.owner_first_name} with {settings.business_name}. Sorry we missed your call. Reply with what {settings.business_type} help you need and we will get you taken care of today.",
        "afternoon": f"Hi, this is {settings.owner_first_name} with {settings.business_name}. Sorry we missed your call. Text us what you need help with and the best address, and we will follow up shortly.",
        "evening": f"Hi, this is {settings.owner_first_name} with {settings.business_name}. Sorry we missed you. Reply with the issue and address, and we will help you get the next step sorted.",
        "after_hours": f"Hi, this is {settings.owner_first_name} with {settings.business_name}. Sorry we missed your call after hours. Reply with what you need, and we will follow up first thing in the morning.",
    }
    return messages.get(scenario, messages["morning"])


async def demo_page() -> HTMLResponse:
    if not get_settings().demo_mode_enabled:
        raise HTTPException(status_code=404, detail="Demo mode disabled")
    return HTMLResponse(DEMO_HTML)


async def demo_missed_call(request: Request) -> dict:
    settings = get_settings()
    if not settings.demo_mode_enabled:
        raise HTTPException(status_code=404, detail="Demo mode disabled")
    if not settings.sms_dry_run:
        raise HTTPException(status_code=403, detail="Browser demo requires SMS_DRY_RUN=true")
    payload = await request.json()
    phone = normalize_phone(payload.get("caller_phone", ""))
    scenario = payload.get("time_scenario", "morning")
    sms_body = sms_for_scenario(scenario)
    form = {
        "CallStatus": payload.get("call_status", "no-answer"),
        "From": phone,
        "To": settings.twilio_phone_number or "+15550001111",
        "CallSid": f"CA-demo-{uuid4()}",
    }
    result = await handle_missed_call(form, sms_override=sms_body)
    return {
        "demo_mode": True,
        "sms_mode": "dry_run" if settings.sms_dry_run else "live",
        "result": result,
        "sms_preview": [{"label": "Missed-call text-back", "to": phone, "body": sms_body}],
    }


def _qualification_for(payload: dict) -> dict:
    scenario = payload.get("reply_scenario", "complete")
    if scenario == "incomplete":
        return {
            "complete": False,
            "name": "Jane Doe",
            "service_type": "AC repair",
            "address": "",
            "urgency_level": "same_day",
            "reply": "Thanks Jane. What service address should we send the team to?",
        }
    return {
        "complete": True,
        "name": "Jane Doe",
        "service_type": "AC repair",
        "address": "123 Main Street",
        "urgency_level": "same_day",
        "reply": "Thanks, we have what we need.",
    }


async def demo_reply(request: Request) -> dict:
    settings = get_settings()
    if not settings.demo_mode_enabled:
        raise HTTPException(status_code=404, detail="Demo mode disabled")
    payload = await request.json()
    phone = normalize_phone(payload.get("caller_phone", ""))
    scenario = payload.get("reply_scenario", "complete")
    body = "STOP" if scenario == "stop" else payload.get("reply_body", "")
    form = {"From": phone, "Body": body, "MessageSid": f"SM-demo-{uuid4()}"}
    qualification = None if scenario == "stop" else _qualification_for(payload)
    result = await handle_sms_reply(form, qualification_override=qualification)
    previews = []
    if result["status"] == "suppressed":
        previews.append({"label": "Opt-out confirmation", "to": phone, "body": "You are opted out and will not receive further texts."})
    elif result["status"] == "lead_created":
        lead = LeadRecord.model_validate(result["lead"])
        previews.extend([
            {"label": "Owner alert preview", "to": settings.demo_owner_phone_number, "body": owner_lead_alert(lead)},
            {"label": "Customer confirmation", "to": phone, "body": lead_confirmation(lead)},
        ])
    else:
        previews.append({"label": "AI intake reply", "to": phone, "body": qualification["reply"] if qualification else ""})
    return {
        "demo_mode": True,
        "sms_mode": "dry_run" if settings.sms_dry_run else "live",
        "result": result,
        "sms_preview": previews,
    }
