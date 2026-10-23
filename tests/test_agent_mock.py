"""End-to-end plumbing with the offline mock coder (no tokens, no network)."""
import json

from knack.agent import LearnConfig, Learner
from knack.runner import LocalRunner


def _cfg(tmp_path, **kw):
    base = dict(task="lift", rounds=3, episodes=3, eval_episodes=6, mock=True, runs_root=str(tmp_path / "runs"),
                save_to_library=False, budget_usd=5.0)
    base.update(kw)
    return LearnConfig(**base)


def test_mock_learn_loop_parallel(tmp_path):
    learner = Learner(_cfg(tmp_path), runner=LocalRunner(workers=3))
    card = learner.run()
    d = learner.dir
    assert (d / "card.json").exists() and (d / "card.html").exists() and (d / "card.md").exists()
    assert card["demonstrations"] == 0 and card["mock"]
    r = card["rounds"]
    assert r[0]["k"] == 0  # deliberately broken v1
    assert r[-1]["k"] >= 2  # fixture v2
    assert card["eval"]["n"] == 6 and card["eval"]["k"] >= 4
    assert card["receipt"]["llm_usd"] > 0
    assert (d / "round_2" / "diff.patch").read_text()
    state = json.loads((d / "state.json").read_text())
    assert state["status"] == "done" and state["eval"]["n"] == 6
    # the summariser was used between rounds and its text reached the coder prompt
    rewrite = json.loads((d / "llm" / "round_2_rewrite.json").read_text())
    assert "Mock summary" in rewrite["messages"][1]["content"]


def test_self_report_reward_is_fooled(tmp_path):
    """v1 returns True without lifting: self-report counts it as success, ground truth does not."""
    learner = Learner(_cfg(tmp_path, reward="self", rounds=1, eval_episodes=3), runner=LocalRunner(workers=3))
    card = learner.run()
    rd = card["rounds"][0]
    assert rd["k"] == rd["self_k"] == 3
    assert rd["gt_k"] == 0


def test_custom_instruction_requires_vlm(tmp_path):
    import pytest

    with pytest.raises(ValueError):
        Learner(_cfg(tmp_path, instruction="wave hello"))
