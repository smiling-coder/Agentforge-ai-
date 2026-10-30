"""Agent orchestrator: plan -> risk -> approve -> execute -> verify -> recover -> remember."""
import threading, time, uuid
from planner import plan
from tools import TOOLS, FALLBACKS, run_tool
from verifier import verify
from security import audit, assess_risk, check_permission
from memory import remember, recall, get_conn

RUNS = {}
MAX_RETRIES = 2          # retry limit per task (3 attempts total)
APPROVAL_TIMEOUT = 120   # seconds to wait for a human decision

def emit(run_id, type_, agent, **data):
    RUNS[run_id]["events"].append({"type": type_, "agent": agent, "ts": time.time(), **data})

def start_run(goal, auto_approve=False, background=True):
    run_id = uuid.uuid4().hex[:8]
    RUNS[run_id] = {"events": [], "done": False, "approvals": {}, "decisions": {}}
    if background:
        threading.Thread(target=run_goal, args=(run_id, goal, auto_approve), daemon=True).start()
    else:
        run_goal(run_id, goal, auto_approve)
    return run_id

def decide(run_id, task_id, approved):
    run = RUNS.get(run_id)
    if not run:
        return False
    run["decisions"][task_id] = bool(approved)
    ev = run["approvals"].get(task_id)
    if ev:
        ev.set()
    return True

def _execute(run_id, task, auto_approve, stats):
    tid, tool = task["id"], task["tool"]
    risk = assess_risk(task)
    emit(run_id, "risk", "Guardian", task_id=tid, risk=risk)
    if not check_permission(tool):
        audit(run_id, "blocked", task)
        emit(run_id, "blocked", "Guardian", task_id=tid, reason="tool not permitted")
        return {"task_id": tid, "status": "blocked", "confidence": 0, "evidence": []}
    if TOOLS[tool]["protected"]:
        approved = auto_approve
        if not auto_approve:
            RUNS[run_id]["approvals"][tid] = threading.Event()
            emit(run_id, "approval_required", "Guardian", task_id=tid, tool=tool, text=task["text"], risk=risk)
            RUNS[run_id]["approvals"][tid].wait(APPROVAL_TIMEOUT)
            approved = RUNS[run_id]["decisions"].get(tid, False)
        audit(run_id, "approval", {"task": tid, "tool": tool, "approved": approved})
        if not approved:
            emit(run_id, "skipped", "Guardian", task_id=tid, reason="human approval denied or timed out")
            return {"task_id": tid, "status": "skipped", "confidence": 0, "evidence": []}
    current, last_err, healed = tool, "", False
    for attempt in range(1, MAX_RETRIES + 2):
        emit(run_id, "task_start", "Executor", task_id=tid, tool=current, attempt=attempt, text=task["text"])
        try:
            out = run_tool(current, task["text"])
            v = verify({**task, "tool": current}, out)
            emit(run_id, "verification", "Verifier", task_id=tid, **v)
            if v["passed"]:
                audit(run_id, "task_done", {"task": tid, "tool": current, "attempt": attempt})
                emit(run_id, "task_done", "Executor", task_id=tid, tool=current, result=str(out)[:300])
                return {"task_id": tid, "status": "done", "tool": current, "result": str(out)[:300],
                        "confidence": v["confidence"], "evidence": v["evidence"], "healed": healed}
            last_err = "verification failed"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            emit(run_id, "task_error", "Executor", task_id=tid, error=last_err, attempt=attempt)
        stats["retries"] += 1
        audit(run_id, "retry", {"task": tid, "attempt": attempt, "error": last_err})
        if attempt >= 2 and current in FALLBACKS:
            emit(run_id, "self_heal", "Recovery", task_id=tid, from_tool=current, to_tool=FALLBACKS[current])
            current, healed = FALLBACKS[current], True
        time.sleep(0.4 * attempt)
    audit(run_id, "task_failed", {"task": tid, "error": last_err})
    emit(run_id, "task_failed", "Recovery", task_id=tid, error=last_err)
    return {"task_id": tid, "status": "failed", "confidence": 0, "evidence": [last_err]}

def run_goal(run_id, goal, auto_approve=False):
    t0, stats = time.time(), {"retries": 0}
    audit(run_id, "goal_received", goal)
    emit(run_id, "memory", "Memory", lessons=recall(goal))
    tasks = plan(goal)
    audit(run_id, "plan_created", tasks)
    emit(run_id, "plan", "Planner", tasks=tasks)
    results = [_execute(run_id, t, auto_approve, stats) for t in tasks]
    passed = sum(r["status"] == "done" for r in results)
    status = "success" if tasks and passed == len(tasks) else "partial" if passed else "failed"
    duration = round(time.time() - t0, 2)
    limits = ["Rule-based planner is used unless an LLM key is configured.",
              "Verification checks are tool-specific and may not catch every wrong answer."]
    if any(r["status"] in ("skipped", "blocked", "failed") for r in results):
        limits.append("Some tasks were skipped, blocked or failed - see timeline.")
    conn = get_conn()
    with conn:
        conn.execute("INSERT OR REPLACE INTO runs VALUES(?,?,?,?,?,?,?,?)",
                     (run_id, t0, goal, status, len(tasks), passed, stats["retries"], duration))
    conn.close()
    if tasks:
        used = [r.get("tool", "-") for r in results]
        remember(goal, f"status={status}; tools={used}; retries={stats['retries']}")
    audit(run_id, "run_finished", {"status": status, "passed": passed, "total": len(tasks)})
    emit(run_id, "final", "Planner", status=status, results=results, duration=duration,
         success_rate=round(passed / len(tasks), 2) if tasks else 0, retries=stats["retries"],
         limitations=limits)
    RUNS[run_id]["done"] = True
    return run_id
