"""Permitted tools. Every tool runs inside a sandbox with an allow-list (feature 2, 21)."""
import ast, operator as op, os, re, time
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from memory import ROOT

SANDBOX = os.path.join(ROOT, "data", "sandbox")
ALLOWED_HOSTS = ("example.com", "wikipedia.org")
_OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
        ast.Mod: op.mod, ast.USub: op.neg}

def safe_eval(expr):
    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        raise ValueError("unsupported expression")
    return ev(ast.parse(expr.strip(), mode="eval").body)

def calculator(text):
    found = [m.strip() for m in re.findall(r"[\d.\s+\-*/()%]{3,}", text)
             if re.search(r"\d", m) and re.search(r"[+\-*/%]", m)]
    if not found:
        raise ValueError("no math expression found")
    expr = max(found, key=len)
    return f"{expr} = {safe_eval(expr)}"

def summarize(text):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:2])

def word_count(text):
    return f"{len(text.split())} words"

def write_note(text):
    os.makedirs(SANDBOX, exist_ok=True)
    path = os.path.join(SANDBOX, f"note_{int(time.time() * 1000)}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return f"Saved note: {path}"

def fetch_url(text):
    m = re.search(r"https?://\S+", text)
    if not m:
        raise ValueError("no URL found")
    host = urlparse(m.group(0)).hostname or ""
    if not any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS):
        raise PermissionError(f"host not allow-listed: {host}")
    req = Request(m.group(0), headers={"User-Agent": "AgentForge-AI"})
    with urlopen(req, timeout=8) as r:
        return r.read(2000).decode("utf-8", "ignore")[:500]

def delete_file(text):
    m = re.search(r"[\w\-]+\.\w+", text)
    if not m:
        raise ValueError("no file name found")
    path = os.path.join(SANDBOX, os.path.basename(m.group(0)))
    if not os.path.exists(path):
        raise FileNotFoundError(f"{m.group(0)} not found in sandbox")
    os.remove(path)
    return f"Deleted: {path}"

def unstable_service(text):
    raise ConnectionError("simulated outage")   # used to demo recovery

def backup_service(text):
    return "Backup service handled the request"

TOOLS = {
    "calculator": {"fn": calculator, "protected": False, "description": "Safe math evaluator"},
    "summarize": {"fn": summarize, "protected": False, "description": "Short extractive summary"},
    "word_count": {"fn": word_count, "protected": False, "description": "Counts words"},
    "write_note": {"fn": write_note, "protected": False, "description": "Saves a note in the sandbox"},
    "fetch_url": {"fn": fetch_url, "protected": True, "description": "Fetches allow-listed web pages"},
    "delete_file": {"fn": delete_file, "protected": True, "description": "Deletes sandbox files"},
    "unstable_service": {"fn": unstable_service, "protected": False, "description": "Always fails (demo)"},
    "backup_service": {"fn": backup_service, "protected": False, "description": "Fallback tool"},
}
FALLBACKS = {"unstable_service": "backup_service"}

def run_tool(name, text):
    return TOOLS[name]["fn"](text)
