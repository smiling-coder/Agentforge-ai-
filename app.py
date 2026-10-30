"""FastAPI server. Run:  uvicorn app:app --reload"""
import json, os, time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import agent, analytics, memory, security

app = FastAPI(title="AgentForge AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class GoalIn(BaseModel):
    goal: str

class ApprovalIn(BaseModel):
    approved: bool

@app.post("/api/run")
def run(body: GoalIn):
    if not body.goal.strip():
        raise HTTPException(400, "goal is empty")
    return {"run_id": agent.start_run(body.goal.strip())}

@app.get("/api/stream/{run_id}")
def stream(run_id: str):
    if run_id not in agent.RUNS:
        raise HTTPException(404, "unknown run")
    def gen():
        i = 0
        while True:
            events = agent.RUNS[run_id]["events"]
            while i < len(events):
                yield f"data: {json.dumps(events[i], default=str)}\n\n"
                i += 1
            if agent.RUNS[run_id]["done"] and i >= len(events):
                break
            time.sleep(0.2)
    return StreamingResponse(gen(), media_type="text/event-stream")

@app.post("/api/approve/{run_id}/{task_id}")
def approve(run_id: str, task_id: int, body: ApprovalIn):
    if not agent.decide(run_id, task_id, body.approved):
        raise HTTPException(404, "unknown run")
    return {"ok": True}

@app.get("/api/analytics")
def get_analytics():
    return analytics.summary()

@app.get("/api/audit")
def get_audit():
    return security.recent_audit()

@app.get("/api/audit/verify")
def verify_audit():
    return security.verify_chain()

@app.get("/api/memory")
def get_memory():
    return memory.all_memory()

FRONTEND = os.path.join(memory.ROOT, "frontend")
if os.path.isdir(FRONTEND):
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
