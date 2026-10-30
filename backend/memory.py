"""Persistent memory + SQLite setup (features 4, 15)."""
import os, re, sqlite3, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCHEMA = """
CREATE TABLE IF NOT EXISTS memory(id INTEGER PRIMARY KEY, ts REAL, goal TEXT, lesson TEXT);
CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, ts REAL, goal TEXT, status TEXT,
  tasks INTEGER, passed INTEGER, retries INTEGER, duration REAL);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, ts REAL, run_id TEXT, event TEXT,
  detail TEXT, prev_hash TEXT, hash TEXT);
"""

def db_path():
    return os.environ.get("AGENTFORGE_DB", os.path.join(ROOT, "data", "agentforge.db"))

def get_conn():
    os.makedirs(os.path.dirname(db_path()), exist_ok=True)
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def _words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def remember(goal, lesson):
    conn = get_conn()
    with conn:
        conn.execute("INSERT INTO memory(ts,goal,lesson) VALUES(?,?,?)", (time.time(), goal, lesson))
    conn.close()

def recall(goal, limit=3):
    """Return past lessons whose goal shares words with the new goal."""
    conn = get_conn()
    rows = conn.execute("SELECT goal, lesson FROM memory ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    gw = _words(goal)
    scored = [(len(gw & _words(r["goal"])), r) for r in rows]
    scored = [s for s in scored if s[0] > 0]
    scored.sort(key=lambda s: -s[0])
    return [{"goal": r["goal"], "lesson": r["lesson"]} for _, r in scored[:limit]]

def all_memory(limit=20):
    conn = get_conn()
    rows = conn.execute("SELECT ts, goal, lesson FROM memory ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
