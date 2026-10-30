import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from planner import plan, select_tool

def test_multi_step_plan():
    tools = [t["tool"] for t in plan("calculate 12*7 and summarize this text")]
    assert tools == ["calculator", "summarize"]

def test_protected_tool_selected():
    assert select_tool("delete old.txt") == "delete_file"

def test_empty_goal():
    assert plan("   ") == []
