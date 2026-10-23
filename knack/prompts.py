"""Prompts for the three model roles. Task-agnostic: no demonstrations, no reference code."""
from __future__ import annotations

import json

from .robot import API_DOC

CODER_SYSTEM = f"""You are Knack's robot programmer. You write a Python skill for a 5-DoF robot arm with a
parallel gripper on a tabletop, then improve it from practice results. Nobody will show you a
demonstration: you learn only from what happens when your code runs.

How practice works
- Your code must define `def run(robot):`. It runs on many randomised layouts of the scene:
  object positions, orientations, masses and friction change every episode. Never hard-code
  coordinates. Read them at run time with robot.observe() or robot.get_pose().
- After each round you get the outcome of every episode, a failure analysis and traces of the
  robot calls your code made. Use them to fix the code. Keep what works.
- Allowed imports: math, numpy, itertools, functools, collections. No file, network or OS access,
  no bare `except:`. Each episode has a simulated-time budget, so no long waits or endless loops.
- Return True if you believe the task succeeded, otherwise False. The return value is logged
  but it is not how success is measured.

{API_DOC}
Good practice (any task)
- Perceive, act, verify, recover: re-read poses after important actions (for example check
  robot.holding() after robot.grasp()) and retry a bounded number of times if a check fails.
- Catch MotionError around moves that might be out of reach and choose another approach.
- Keep moves near objects slow (speed 0.05-0.10) and travel moves at the default speed.

Reply format (always both parts):
<notes>
3-8 short bullets: what the last results taught you and what you changed. Carry forward
useful facts from earlier notes.
</notes>
```python
# the complete skill module
```
"""


def first_user(instruction: str, title: str, example_obs: dict, library: list | None = None, probe_log: str | None = None) -> str:
    parts = [
        f"Task: {instruction}",
        "",
        f"Scene: {title}. Example observation from one random layout (positions differ every episode):",
        json.dumps(example_obs, indent=1),
    ]
    if library:
        parts += ["", "Verified skills from earlier tasks (you may reuse their helper functions):"]
        for item in library:
            parts += [f"# skill for: {item['instruction']} (held-out success {item.get('success_text', '?')})", "```python", item["code"].strip(), "```"]
    if probe_log:
        parts += ["", "Log of your exploratory tool calls on one layout:", probe_log]
    parts += ["", "Write the first version of the skill."]
    return "\n".join(parts)


REWARD_NOTES = {
    "gt": "Success is measured by the simulator's ground-truth check.",
    "vlm": ("Success is judged by a vision model looking at camera frames of the final scene. It can be wrong. "
            "'uncertain' means the judge abstained."),
    "self": "Success is whatever your own code returned. Nothing else checked the outcome.",
}


def revise_user(instruction: str, round_k: int, reward: str, n_ok: int, n: int, episode_lines: list[str], summary: str,
                traces: str, notes: str, history: list[str], code: str) -> str:
    return "\n".join([
        f"Task: {instruction}",
        "",
        f"Round {round_k} results: {n_ok}/{n} episodes counted as success.",
        REWARD_NOTES[reward],
        "",
        "Per-episode outcomes:",
        *episode_lines,
        "",
        "Failure analysis:",
        summary or "(no failures to analyse)",
        "",
        "Traces of some failed episodes (robot calls with results; t is simulated seconds):",
        traces or "(none)",
        "",
        "Your notes so far:",
        notes or "(none)",
        "",
        "Previous rounds:",
        *(history or ["(this was the first round)"]),
        "",
        "Current code:",
        "```python",
        code.strip(),
        "```",
        "",
        "Fix the failures without breaking what works. Reply with <notes> and the complete new code.",
    ])


FORMAT_REMINDER = ("Your reply did not contain a usable ```python block defining run(robot). Reply again with "
                   "<notes>...</notes> followed by the complete code in a ```python block.")


def compile_error_user(error: str) -> str:
    return (f"The code was rejected before running: {error}\n"
            "Fix it and reply with <notes> and the complete code.")


SUMMARIZER_SYSTEM = """You analyse robot practice logs for a programmer. Be concrete and brief.
You never write code. You point at line numbers and robot calls."""


def summarizer_user(instruction: str, code: str, episode_lines: list[str], traces: str) -> str:
    numbered = "\n".join(f"{i + 1:3d}| {line}" for i, line in enumerate(code.strip().splitlines()))
    return "\n".join([
        f"Task: {instruction}",
        "",
        "Skill code (numbered):",
        numbered,
        "",
        "Per-episode outcomes:",
        *episode_lines,
        "",
        "Traces of failed episodes:",
        traces,
        "",
        "Group the failures into modes. For each mode give: how many episodes, the likely root cause "
        "in the code (cite line numbers), and one concrete fix. At most 180 words. No code.",
    ])


JUDGE_SYSTEM = """You are a strict referee for robot manipulation episodes in a simulated tabletop scene.
You see camera frames. Decide whether the task is completed in the FINAL state.
Answer only with a JSON object."""

VIEW_LABELS = {
    "start_front": "START, front camera",
    "end_front": "END, front camera",
    "end_side": "END, low side camera (good for heights and stacking)",
    "end_overhead": "END, overhead camera (top-down, good for positions)",
}


def judge_text(instruction: str, views: list[str]) -> str:
    listing = "\n".join(f"{i + 1}) {VIEW_LABELS.get(v, v)}" for i, v in enumerate(views))
    return (f"Task given to the robot: {instruction}\n\nFrames in order:\n{listing}\n\n"
            "Respond with JSON only: {\"success\": true or false, \"confidence\": number from 0 to 1, "
            "\"reason\": \"one short sentence\"}. If the frames do not show enough to decide, use a confidence below 0.6.")


PROBE_SYSTEM = f"""You are exploring a robot scene before writing a skill. Call the tools to look around and try
motions. Be efficient: at most a few calls. When you have learned enough, reply with a short plain-text
summary of what you learned (positions, what worked, what failed).

{API_DOC}"""
