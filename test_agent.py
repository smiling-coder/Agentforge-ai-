import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import pytest
import agent, security
from memory import get_conn

@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTFORGE_DB", str(tmp_path / "t.db"))
    monkeypatch.setattr(agent.time, "sleep", lambda s: None)

def final(run_id):
    return [e for e in agent.RUNS[run_id]["events"] if e["type"] == "final"][0]

def test_successful_run():
    rid = agent.start_run("calculate 12*7", auto_approve=True, background=False)
    f = final(rid)
    assert f["status"] == "success" and f["success_rate"] == 1.0

def test_protected_action_denied_without_approval(monkeypatch):
    monkeypatch.setattr(agent, "APPROVAL_TIMEOUT", 0.05)
    rid = agent.start_run("delete missing.txt", background=False)
    assert final(rid)["results"][0]["status"] == "skipped"

def test_failure_recovery_uses_fallback():
    rid = agent.start_run("simulate unstable failure", auto_approve=True, background=False)
    f = final(rid)
    assert f["results"][0]["status"] == "done" and f["retries"] >= 1
    assert any(e["type"] == "self_heal" for e in agent.RUNS[rid]["events"])

def test_audit_chain_detects_tampering():
    agent.start_run("calculate 1+1", auto_approve=True, background=False)
    assert security.verify_chain()["valid"]
    conn = get_conn()
    with conn:
        conn.execute("UPDATE audit SET detail='tampered' WHERE id=1")
    conn.close()
    assert not security.verify_chain()["valid"]
