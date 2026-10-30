# Architecture

```
Browser (HTML/CSS/JS) --POST /api/run--> FastAPI (app.py) --thread--> agent.run_goal
      ^                                                         |
      |--- SSE /api/stream/{run} <----- event list <------------+
                                                                |
 planner.plan -> security.assess_risk -> [human approval] -> tools.run_tool
        -> verifier.verify -> retry / fallback (self-heal) -> memory + audit + analytics (SQLite)
```

## Workflow (matches the 12-step spec)
1 goal -> 2-3 planner -> 4 risk + permission -> 5 tool selection -> 6 approval -> 7 execution (retry limit 2)
-> 8 verification -> 9 recovery/fallback -> 10 memory + audit -> 11 analytics -> 12 final report with limitations.

## Modules
- `planner.py` rule-based or LLM plan (invalid tools discarded).
- `tools.py` registry; `protected` tools need approval; fetch limited to allow-listed hosts; file ops limited to `data/sandbox`.
- `verifier.py` independent re-checks (recompute math, check file exists/deleted) -> confidence + evidence.
- `security.py` default-deny permissions, risk score, SHA-256 hash-chained audit log; editing any row breaks verification.
- `memory.py` SQLite tables `memory`, `runs`, `audit`; keyword recall.
- `analytics.py` success rate, retries, average duration.

## Limits
Runs are held in process memory (restart clears live streams; history stays in SQLite). Single-process design.
