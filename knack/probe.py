"""Optional exploration phase: the coder drives the robot with tool calls on one
layout before writing code (perceive, act, verify). The log goes into the
first coding prompt."""
from __future__ import annotations

import json
from pathlib import Path

from .prompts import PROBE_SYSTEM
from .tools import TOOL_SPECS, dispatch


def run_probe(llm, model: str, task, instruction: str, seed: int, run_dir: Path, max_steps: int = 8) -> str:
    from .robot import SimRobot
    from .sim import SimEnv

    env = SimEnv(task, seed, render_size=(64, 48))
    robot = SimRobot(env, max_time=task.max_time)
    messages = [{"role": "system", "content": PROBE_SYSTEM},
                {"role": "user", "content": f"Task you will later write a skill for: {instruction}\nExplore with the tools."}]
    log = []
    final = ""
    for step in range(max_steps):
        reply = llm.chat("probe", model, messages, temperature=0.2, max_tokens=4000, tools=TOOL_SPECS)
        if not reply.tool_calls:
            final = reply.text.strip()
            break
        messages.append({"role": "assistant", "content": reply.text or "", "tool_calls": [
            {"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments"]}} for tc in reply.tool_calls]})
        for tc in reply.tool_calls:
            out = dispatch(robot, tc["name"], tc["arguments"])
            text = json.dumps(out, default=str)[:3000]
            log.append(f"{tc['name']}({tc['arguments']}) -> {text[:400]}")
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": text})
            if isinstance(out, dict) and out.get("halted"):
                break
    env.close()
    (Path(run_dir) / "probe_log.txt").write_text("\n".join(log) + "\n\nSUMMARY:\n" + final, encoding="utf-8")
    return "\n".join(log[-12:]) + (f"\nYour summary: {final}" if final else "")
