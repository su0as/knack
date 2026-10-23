"""The reference fixtures must solve every scene: proves physics, IK, grasping and the checks work.

These fixtures are never shown to the coding agent (see test_prompts_have_no_oracle_code).
"""
import pytest

from knack.oracles import ORACLES
from knack.runner import run_inline

MIN_OK = {"lift": 4, "place": 4, "stack": 3, "tray": 4, "sort": 3, "push": 3}


@pytest.mark.parametrize("task_id", list(ORACLES))
def test_reference_fixture_solves_scene(task_id, tmp_path):
    specs = [{"task": task_id, "seed": 900_000 + i, "code": ORACLES[task_id], "render": {"live": False, "keyframes": False}}
             for i in range(4)]
    res = run_inline(specs, tmp_path)
    k = sum(bool(r["success_gt"]) for r in res)
    detail = [(r["seed"], r["success_gt"], r.get("error"), r.get("metrics"), r.get("halted")) for r in res]
    assert k >= MIN_OK[task_id], detail
    for r in res:
        assert r["error"] is None or r["error"]["type"] not in ("CompileError", "HarnessError"), r["error"]


def test_prompts_have_no_oracle_code():
    from knack import prompts

    obs = {"objects": {}, "fixtures": {}}
    texts = [prompts.CODER_SYSTEM, prompts.first_user("x", "y", obs), prompts.SUMMARIZER_SYSTEM, prompts.JUDGE_SYSTEM, prompts.PROBE_SYSTEM]
    for code in ORACLES.values():
        body = [ln.strip() for ln in code.splitlines() if "robot." in ln]
        for t in texts:
            for ln in body:
                assert ln not in t
