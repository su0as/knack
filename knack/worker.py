"""Run one skill on one randomised scene and write result.json.

Also a CLI used inside Nebius Serverless Jobs:
    python -m knack.worker --batch batch.json --out results/ --workers 16
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

from .safety import Limits, RobotHalt, SafetyShield


def run_episode(spec: dict, out_dir) -> dict:
    """spec: {task, seed, code, max_time?, render?: {live, keyframes, gif, width, height}, obs_noise?, realism?}"""
    from .recorder import Recorder
    from .robot import SimRobot
    from .sandbox import SkillCompileError, compile_skill, skill_traceback
    from .sim import SimEnv
    from .tasks import get_task

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    task = get_task(spec["task"])
    render = spec.get("render") or {}
    size = (int(render.get("width", 320)), int(render.get("height", 240)))
    from .sim import REALISM

    realism = spec.get("realism") or "sim"
    env = SimEnv(task, int(spec["seed"]), render_size=size, realism=realism)
    shield = SafetyShield(Limits(), env.geometry)
    max_time = float(spec.get("max_time") or task.max_time)
    robot = SimRobot(env, shield, max_time=max_time, obs_noise=float(spec.get("obs_noise", REALISM[realism]["pos_noise"])),
                     yaw_noise=REALISM[realism]["yaw_noise"])
    rec = None
    if render.get("live", True) or render.get("keyframes", True) or render.get("gif"):
        rec = Recorder(env, out, live_every=0.5 if render.get("live", True) else 0.0,
                       gif_every=0.1 if render.get("gif") else None, size=size)
    frames = {}
    if rec and render.get("keyframes", True):
        frames.update(rec.keyframe("start"))
    initial = robot.snapshot(noisy=False)
    printed: list[str] = []

    def printer(*a, **k):
        if len(printed) < 60:
            printed.append(" ".join(str(x) for x in a)[:300])

    result: dict = {
        "task": task.id,
        "seed": int(spec["seed"]),
        "error": None,
        "self_report": None,
    }
    try:
        fn = compile_skill(spec["code"], printer=printer)
        ret = fn(robot)
        result["returned"] = repr(ret)[:200]
        if isinstance(ret, bool):
            result["self_report"] = ret
        elif isinstance(ret, dict) and isinstance(ret.get("success"), bool):
            result["self_report"] = ret["success"]
    except SkillCompileError as e:
        result["error"] = {"type": "CompileError", "message": str(e)[:1500], "traceback": ""}
    except RobotHalt as e:
        result["error"] = {"type": type(e).__name__, "message": str(e)[:500], "traceback": skill_traceback(e)}
    except Exception as e:  # skill bug
        result["error"] = {"type": type(e).__name__, "message": str(e)[:500], "traceback": skill_traceback(e)}
    # let the scene come to rest without new commands
    try:
        env.step_seconds(0.5)
    except Exception:
        pass
    ok, metrics = task.success(env)
    if rec and render.get("keyframes", True):
        frames.update(rec.keyframe("end"))
    gif = rec.save_gif() if (rec and render.get("gif")) else None
    final = robot.snapshot(noisy=False)
    result.update({
        "success_gt": bool(ok),
        "metrics": metrics,
        "trace": robot.trace,
        "n_calls": robot._calls,
        "printed": printed,
        "safety_events": shield.events,
        "safety_summary": shield.summary(),
        "halted": robot.halted,
        "sim_time": round(env.time, 2),
        "wall_time": round(time.time() - t0, 2),
        "initial_obs": initial,
        "final_obs": final,
        "frames": frames,
        "gif": gif,
        "render_error": env.render_error,
        "layout": {k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in env.layout.items()},
    })
    env.close()
    write_result(out, result)
    return result


def write_result(out_dir, result: dict):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / "result.json.tmp"
    tmp.write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    os.replace(tmp, out / "result.json")


def failed_result(spec: dict, kind: str, message: str) -> dict:
    return {
        "task": spec.get("task"),
        "seed": int(spec.get("seed", -1)),
        "error": {"type": kind, "message": message, "traceback": ""},
        "self_report": None,
        "success_gt": False,
        "metrics": {},
        "trace": [],
        "safety_events": [],
        "safety_summary": {},
        "frames": {},
        "sim_time": None,
        "wall_time": None,
    }


def child_main(specs: list, out_dirs: list):
    """Process entry point (must be importable for the 'spawn' start method)."""
    for spec, out in zip(specs, out_dirs):
        try:
            run_episode(spec, out)
        except BaseException as e:  # harness crash: record it, keep going
            write_result(out, failed_result(spec, "HarnessError", f"{type(e).__name__}: {e}\n{traceback.format_exc()[-1500:]}"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run a batch of Knack episodes (used inside Nebius Serverless Jobs).")
    ap.add_argument("--batch", required=True, help="JSON file: {code, task, seeds, max_time?, render?}")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args(argv)
    from .runner import LocalRunner

    batch = json.loads(Path(args.batch).read_text(encoding="utf-8"))
    specs = [
        {"task": batch["task"], "seed": s, "code": batch["code"], "max_time": batch.get("max_time"),
         "render": batch.get("render", {"live": False, "keyframes": True}), "obs_noise": batch.get("obs_noise", 0.002),
         "realism": batch.get("realism", "sim")}
        for s in batch["seeds"]
    ]
    t0 = time.time()
    results = LocalRunner(workers=args.workers).run_batch(specs, Path(args.out))
    summary = {
        "n": len(results),
        "success_gt": sum(1 for r in results if r.get("success_gt")),
        "wall_time": round(time.time() - t0, 2),
        "workers": args.workers,
        "cpu_count": os.cpu_count(),
    }
    (Path(args.out) / "batch_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
