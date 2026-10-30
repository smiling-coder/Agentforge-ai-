"""Autonomous goal planner (feature 1, 24). Uses an LLM if configured, else rules."""
import json, os, re
from urllib.request import urlopen, Request
from tools import TOOLS

RULES = [
    ("delete_file", r"delete|remove"),
    ("fetch_url", r"https?://|fetch|download"),
    ("calculator", r"calculat|comput|\d+\s*[+\-*/%]\s*\d+"),
    ("unstable_service", r"unstable|flaky|failure"),
    ("write_note", r"\bnote\b|\bsave\b|\bwrite\b"),
    ("word_count", r"count|how many words"),
    ("summarize", r"summar|shorten|tl;dr"),
]

def select_tool(text):
    t = text.lower()
    for tool, pattern in RULES:
        if re.search(pattern, t):
            return tool
    return "summarize"

def split_goal(goal):
    parts = re.split(r"\s*(?:,|;|\bthen\b|\band\b)\s*", goal.strip(), flags=re.I)
    return [p for p in parts if p]

def rule_plan(goal):
    return [{"id": i + 1, "text": p, "tool": select_tool(p)} for i, p in enumerate(split_goal(goal))]

def llm_plan(goal):
    """OpenAI-compatible chat endpoint. Returns None on any problem."""
    key = os.environ.get("LLM_API_KEY")
    if not key:
        return None
    try:
        base = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
        prompt = ("Break the goal into small tasks. Reply ONLY with JSON: "
                  '[{"text": "...", "tool": "<one of %s>"}]. Goal: %s' % (", ".join(TOOLS), goal))
        body = json.dumps({"model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
                           "messages": [{"role": "user", "content": prompt}]}).encode()
        req = Request(base + "/chat/completions", body,
                      {"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        with urlopen(req, timeout=20) as r:
            content = json.load(r)["choices"][0]["message"]["content"]
        items = json.loads(re.search(r"\[.*\]", content, re.S).group(0))
        tasks = [{"id": i + 1, "text": it["text"], "tool": it["tool"]}
                 for i, it in enumerate(items) if it.get("tool") in TOOLS]
        return tasks or None
    except Exception:
        return None

def plan(goal):
    if not goal or not goal.strip():
        return []
    return llm_plan(goal) or rule_plan(goal)
