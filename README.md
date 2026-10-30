# AgentForge AI
**Build. Think. Act. Verify. Evolve.**

An AI agent platform that takes a goal, plans tasks, runs only **permitted tools**, **verifies** real results,
**recovers** from failures within retry limits, asks a **human** before protected actions, and keeps a
**tamper-evident audit trail**.

**live demo :**https://agentforge-ai-2.onrender.com

## Run locally (Windows / VS Code)
```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```
Open http://127.0.0.1:8000 (the backend also serves the frontend).

## Run tests
```
pip install -r backend/requirements.txt
pytest
```

## What is implemented (honest status)
| # | Feature | Where |
|---|---------|-------|
| 1 | Autonomous Goal Planner (rule-based; optional LLM) | `planner.py` |
| 2 | Dynamic tool selection & execution | `planner.py`, `tools.py` |
| 3, 16 | Self-verification, confidence & evidence | `verifier.py` |
| 4, 15 | Persistent memory (recalled on similar goals) | `memory.py` |
| 5 | Live execution monitor (Server-Sent Events) | `app.py`, `script.js` |
| 6, 19 | Retry limits, fallback tool (self-healing) | `agent.py` |
| 8 | Human approval for protected tools | `agent.py`, UI buttons |
| 9 | Performance analytics | `analytics.py` |
| 10, 22 | Audit trail with SHA-256 hash chain + verify | `security.py` |
| 14 | Basic predictive risk scoring | `security.py` |
| 21 | Zero-trust: default-deny tools, sandbox, URL allow-list | `security.py`, `tools.py` |
| 7 (basic) | Role-separated agents: Planner, Executor, Verifier, Guardian, Recovery | `agent.py` |

**Roadmap (not built yet):** swarm, knowledge graph, counterfactual planning, digital twin, visual workflow
builder, model router, replay, red-team lab. Final scope must follow the official hackathon rules.

## Optional LLM
Copy `.env.example` to `.env`, set `LLM_API_KEY` (any OpenAI-compatible API) and export it before starting.
Without a key the rule-based planner is used.

## Deploy
Simplest: deploy `backend/` on Render/Railway (start command `uvicorn app:app --host 0.0.0.0 --port $PORT`);
it serves the frontend too. For a separate frontend host, set `window.AGENTFORGE_API` in `index.html`.
