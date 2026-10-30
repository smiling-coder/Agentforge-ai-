// If the backend is hosted elsewhere, set window.AGENTFORGE_API = "https://your-backend" before this script.
const API = window.AGENTFORGE_API || "";
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const tl = $("#timeline");

function add(cls, who, title, body = "") {
  const d = document.createElement("div");
  d.className = "ev " + cls;
  d.innerHTML = `<b>${esc(who)}</b><div>${title}</div>${body ? `<pre>${body}</pre>` : ""}`;
  tl.appendChild(d);
  d.scrollIntoView({ block: "nearest" });
  return d;
}

function render(ev, runId) {
  const t = ev.task_id ? `Task ${ev.task_id}: ` : "";
  switch (ev.type) {
    case "memory":
      return add("info", ev.agent, "Recalled memory", ev.lessons.length ? esc(ev.lessons.map((l) => `• ${l.goal} → ${l.lesson}`).join("\n")) : "No related past runs.");
    case "plan":
      return add("info", ev.agent, "Plan created", esc(ev.tasks.map((x) => `${x.id}. ${x.text}  [${x.tool}]`).join("\n")));
    case "risk":
      return add(ev.risk.level === "low" ? "ok" : "warn", ev.agent, `${t}Risk: ${ev.risk.level} (${ev.risk.score})`);
    case "approval_required": {
      const d = add("warn", ev.agent, `${t}Approval needed for <code>${esc(ev.tool)}</code>`, esc(ev.text));
      const box = document.createElement("div");
      box.className = "row";
      box.innerHTML = `<button class="allow">Approve</button><button class="deny">Deny</button>`;
      box.querySelectorAll("button").forEach((b, i) => (b.onclick = async () => {
        await fetch(`${API}/api/approve/${runId}/${ev.task_id}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ approved: i === 0 }) });
        box.remove();
      }));
      d.appendChild(box);
      return d;
    }
    case "task_start": return add("info", ev.agent, `${t}Running <code>${esc(ev.tool)}</code> (attempt ${ev.attempt})`);
    case "task_error": return add("bad", ev.agent, `${t}Error`, esc(ev.error));
    case "verification": return add(ev.passed ? "ok" : "bad", ev.agent, `${t}Verification — confidence ${ev.confidence}`, esc(ev.evidence.join("\n")));
    case "self_heal": return add("warn", ev.agent, `${t}Self-healing: switching ${esc(ev.from_tool)} → ${esc(ev.to_tool)}`);
    case "task_done": return add("ok", ev.agent, `${t}Done`, esc(ev.result));
    case "task_failed": return add("bad", ev.agent, `${t}Failed after retry limit`, esc(ev.error));
    case "skipped": case "blocked": return add("bad", ev.agent, `${t}${ev.type}`, esc(ev.reason));
    case "final":
      return add(ev.status === "success" ? "ok" : "warn", "Final report",
        `Status: <b>${esc(ev.status)}</b> · success rate ${ev.success_rate} · retries ${ev.retries} · ${ev.duration}s`,
        esc("Limitations:\n- " + ev.limitations.join("\n- ")));
  }
}

async function run(goal) {
  goal = goal.trim();
  if (!goal) return;
  tl.innerHTML = "";
  $("#runBtn").disabled = true;
  try {
    const r = await fetch(API + "/api/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ goal }) });
    const { run_id } = await r.json();
    const es = new EventSource(`${API}/api/stream/${run_id}`);
    es.onmessage = (m) => {
      const ev = JSON.parse(m.data);
      render(ev, run_id);
      if (ev.type === "final") { es.close(); $("#runBtn").disabled = false; loadAll(); }
    };
    es.onerror = () => { es.close(); $("#runBtn").disabled = false; };
  } catch (e) {
    add("bad", "System", "Could not reach the backend", esc(e.message));
    $("#runBtn").disabled = false;
  }
}

async function loadAll() {
  try {
    const a = await (await fetch(API + "/api/analytics")).json();
    $("#stats").innerHTML = [["Runs", a.total_runs], ["Task success", Math.round(a.task_success_rate * 100) + "%"],
      ["Retries", a.total_retries], ["Avg time", a.avg_duration_s + "s"]]
      .map(([k, v]) => `<div class="stat"><span>${v}</span><small>${k}</small></div>`).join("");
    $("#recent").innerHTML = a.recent_runs.map((r) => `<li>${esc(r.goal)} — <b>${esc(r.status)}</b> (${r.passed}/${r.tasks})</li>`).join("");
    const au = await (await fetch(API + "/api/audit")).json();
    $("#audit").innerHTML = au.slice(0, 8).map((x) => `<li>#${x.id} ${esc(x.event)} · ${esc(x.hash.slice(0, 12))}…</li>`).join("");
    const m = await (await fetch(API + "/api/memory")).json();
    $("#memory").innerHTML = m.slice(0, 6).map((x) => `<li>${esc(x.goal)}<br><span class="muted">${esc(x.lesson)}</span></li>`).join("");
  } catch (e) { /* backend not ready yet */ }
}

$("#runBtn").onclick = () => run($("#goal").value);
$("#goal").addEventListener("keydown", (e) => e.key === "Enter" && run(e.target.value));
document.querySelectorAll(".ex").forEach((a) => (a.onclick = (e) => { e.preventDefault(); $("#goal").value = a.textContent; }));
$("#verifyBtn").onclick = async () => {
  const v = await (await fetch(API + "/api/audit/verify")).json();
  $("#chain").textContent = v.valid ? `✔ Chain valid (${v.entries} entries)` : `✘ Tampering detected at entry #${v.broken_at}`;
};
loadAll();
