"""Self-verification + confidence/evidence engine (features 3, 16)."""
import os
from tools import safe_eval

def verify(task, result):
    tool, text = task["tool"], task["text"]
    checks = []   # (description, passed)
    checks.append(("result is non-empty", bool(result and str(result).strip())))
    try:
        if tool == "calculator":
            expr, val = result.rsplit(" = ", 1)
            checks.append(("recomputed answer matches", abs(safe_eval(expr) - float(val)) < 1e-9))
        elif tool == "word_count":
            checks.append(("count recomputed independently", result == f"{len(text.split())} words"))
        elif tool == "write_note":
            path = result.split(": ", 1)[1]
            checks.append(("note file exists on disk", os.path.exists(path)))
        elif tool == "delete_file":
            path = result.split(": ", 1)[1]
            checks.append(("file no longer exists", not os.path.exists(path)))
        elif tool == "summarize":
            checks.append(("summary not longer than input", len(result) <= max(len(text), 1)))
    except Exception as e:
        checks.append((f"verification error: {e}", False))
    passed = all(ok for _, ok in checks)
    confidence = round(sum(ok for _, ok in checks) / len(checks), 2)
    evidence = [("✔ " if ok else "✘ ") + d for d, ok in checks]
    return {"passed": passed, "confidence": confidence, "evidence": evidence}
