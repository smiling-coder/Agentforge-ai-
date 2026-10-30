"""Zero-trust permissions, risk scoring and tamper-evident audit ledger (features 8, 10, 14, 21, 22)."""
import hashlib, json, threading, time
from memory import get_conn
from tools import TOOLS

_lock = threading.Lock()
RISKY_WORDS = ("delete", "remove", "password", "payment", "send", "format")

def check_permission(tool):
    """Default deny: only registered tools may run."""
    return tool in TOOLS

def assess_risk(task):
    score = 50 if TOOLS.get(task["tool"], {}).get("protected") else 0
    score += 30 if any(w in task["text"].lower() for w in RISKY_WORDS) else 0
    level = "high" if score >= 70 else "medium" if score >= 40 else "low"
    return {"score": score, "level": level}

def _hash(prev, ts, run_id, event, detail):
    return hashlib.sha256(f"{prev}|{ts}|{run_id}|{event}|{detail}".encode()).hexdigest()

def audit(run_id, event, detail=""):
    if not isinstance(detail, str):
        detail = json.dumps(detail, default=str)
    with _lock:
        conn = get_conn()
        row = conn.execute("SELECT hash FROM audit ORDER BY id DESC LIMIT 1").fetchone()
        prev, ts = (row["hash"] if row else "GENESIS"), time.time()
        with conn:
            conn.execute("INSERT INTO audit(ts,run_id,event,detail,prev_hash,hash) VALUES(?,?,?,?,?,?)",
                         (ts, run_id, event, detail, prev, _hash(prev, ts, run_id, event, detail)))
        conn.close()

def verify_chain():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM audit ORDER BY id").fetchall()
    conn.close()
    prev = "GENESIS"
    for r in rows:
        if r["prev_hash"] != prev or r["hash"] != _hash(prev, r["ts"], r["run_id"], r["event"], r["detail"]):
            return {"valid": False, "broken_at": r["id"], "entries": len(rows)}
        prev = r["hash"]
    return {"valid": True, "entries": len(rows)}

def recent_audit(limit=30):
    conn = get_conn()
    rows = conn.execute("SELECT id, ts, run_id, event, detail, hash FROM audit ORDER BY id DESC LIMIT ?",
                        (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
