"""Agent performance analytics (feature 9)."""
from memory import get_conn

def summary():
    conn = get_conn()
    r = conn.execute("SELECT COUNT(*) n, COALESCE(SUM(tasks),0) t, COALESCE(SUM(passed),0) p, "
                     "COALESCE(SUM(retries),0) rt, COALESCE(AVG(duration),0) d FROM runs").fetchone()
    audits = conn.execute("SELECT COUNT(*) c FROM audit").fetchone()["c"]
    recent = [dict(x) for x in conn.execute(
        "SELECT id, goal, status, tasks, passed, retries, duration FROM runs ORDER BY ts DESC LIMIT 8")]
    conn.close()
    return {"total_runs": r["n"], "total_tasks": r["t"],
            "task_success_rate": round(r["p"] / r["t"], 2) if r["t"] else 0,
            "total_retries": r["rt"], "avg_duration_s": round(r["d"], 2),
            "audit_events": audits, "recent_runs": recent}
