import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from verifier import verify

def test_calculator_correct():
    assert verify({"tool": "calculator", "text": "12*7"}, "12*7 = 84")["passed"]

def test_calculator_wrong_answer_caught():
    v = verify({"tool": "calculator", "text": "12*7"}, "12*7 = 80")
    assert not v["passed"] and v["confidence"] < 1

def test_empty_result_fails():
    assert not verify({"tool": "summarize", "text": "hi"}, "")["passed"]

def test_word_count():
    assert verify({"tool": "word_count", "text": "a b c"}, "3 words")["passed"]
