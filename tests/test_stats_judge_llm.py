import pytest

from knack.config import MODELS, resolve_model
from knack.judge import parse_verdict
from knack.llm import BudgetExceeded, Ledger, MockLLM, strip_thinking
from knack.stats import judge_metrics, wilson


def test_wilson_known_values():
    p, lo, hi = wilson(8, 10)
    assert p == 0.8
    assert lo == pytest.approx(0.4902, abs=1e-3)
    assert hi == pytest.approx(0.9433, abs=1e-3)
    assert wilson(0, 0) == (0.0, 0.0, 1.0)
    _, lo, hi = wilson(100, 100)
    assert hi == 1.0 and lo > 0.95


def test_judge_metrics():
    m = judge_metrics([(True, True), (True, False), (False, False), (False, True), (True, None)])
    assert m["abstained"] == 1 and m["decided"] == 4
    assert m["accuracy"] == 0.5
    assert m["false_success_rate"] == 0.5


@pytest.mark.parametrize("text,succ,abst", [
    ('{"success": true, "confidence": 0.9, "reason": "cube is high"}', True, False),
    ('Sure. ```json\n{"success": false, "confidence": 0.8, "reason": "on table"}\n```', False, False),
    ('{"success": true, "confidence": 0.3, "reason": "hard to see"}', None, True),
    ("I cannot tell", None, True),
    ('success: true, confidence: 0.95', True, False),
])
def test_parse_verdict(text, succ, abst):
    v = parse_verdict(text, threshold=0.6)
    assert v.success == succ and v.abstained == abst


def test_strip_thinking():
    assert strip_thinking("<think>hmm</think>answer") == ("answer", "hmm")
    assert strip_thinking("reasoning here</think>\nfinal")[0] == "final"


def test_costs_and_budget(tmp_path):
    m = MODELS["ultra"]
    assert m.cost(1_000_000, 1_000_000) == pytest.approx(4.0)
    assert m.cost(1_000_000, 0, cached_tokens=1_000_000) == pytest.approx(0.12)
    assert resolve_model("nvidia/Nemotron-3.5-Super-VL").alias == "super-vl"
    led = Ledger(tmp_path / "l.jsonl", budget_usd=0.00001)
    llm = MockLLM(led, lambda role, msgs: "x" * 4000)
    llm.chat("coder", "ultra", [{"role": "user", "content": "hi" * 100}])
    with pytest.raises(BudgetExceeded):
        llm.chat("coder", "ultra", [{"role": "user", "content": "hi"}])
    assert led.summary()["by_role"]["coder"]["calls"] == 1


def test_truncated_leaked_thinking_is_not_an_answer(tmp_path):
    """Live Token Factory behaviour (23 Oct 2026): a reasoning model cut off at max_tokens returned its
    unfinished thought as plain content. The client must not pass that on as the answer."""
    from types import SimpleNamespace as NS

    from knack.llm import LLMClient

    client = LLMClient(Ledger(tmp_path / "l.jsonl"), key="test-key")
    usage = NS(prompt_tokens=100, completion_tokens=4000, prompt_tokens_details=None,
               completion_tokens_details=NS(reasoning_tokens=0))
    leaked = NS(choices=[NS(finish_reason="length", message=NS(content="Here's a thinking process:\n1. Analyse...", tool_calls=None))],
                usage=usage)
    r = client._finish("summarizer", __import__("knack.config", fromlist=["resolve_model"]).resolve_model("lightning"), leaked, 1.0)
    assert r.text == "" and "thinking process" in r.reasoning and r.finish_reason == "length"
    normal = NS(choices=[NS(finish_reason="stop", message=NS(content="Mode 1: gripper closes high (line 12).", tool_calls=None))],
                usage=NS(prompt_tokens=100, completion_tokens=20, prompt_tokens_details=None, completion_tokens_details=None))
    r2 = client._finish("summarizer", __import__("knack.config", fromlist=["resolve_model"]).resolve_model("lightning"), normal, 1.0)
    assert r2.text.startswith("Mode 1") and r2.finish_reason == "stop"
