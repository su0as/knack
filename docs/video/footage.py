"""Re-run the hero run's real skills in the simulator and save every frame (for the demo video).

Round 1 skill on the round 1 practice layouts (seeds 1000-1007) and the final skill on the round 2 layouts
(seeds 2000-2007), with OpenCV 5 vision perception, exactly as in run 20261027-012153-lift-super-gt-vision.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from knack.recorder import Recorder  # noqa: E402
from knack.robot import SimRobot  # noqa: E402
from knack.safety import Limits, RobotHalt, SafetyShield  # noqa: E402
from knack.sandbox import compile_skill  # noqa: E402
from knack.sim import REALISM, SimEnv  # noqa: E402
from knack.tasks import get_task  # noqa: E402
from knack.vision import VisionPerception  # noqa: E402

HERE = Path(__file__).parent
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "footage")


def episode(code, seed, size, every, camera, out_dir):
    task = get_task("lift")
    env = SimEnv(task, seed, render_size=size, realism="vision")
    shield = SafetyShield(Limits(), env.geometry)
    vision = VisionPerception(env)
    robot = SimRobot(env, shield, max_time=task.max_time, obs_noise=REALISM["vision"]["pos_noise"],
                     yaw_noise=REALISM["vision"]["yaw_noise"], vision=vision)
    rec = Recorder(env, out_dir / "_tmp", live_every=0.0, gif_every=every, live_camera=camera, size=size, gif_size=size)
    err = None
    try:
        compile_skill(code)(robot)
    except (Exception, RobotHalt) as e:
        err = f"{type(e).__name__}: {e}"
    env.step_seconds(0.6)
    ok, metrics = task.success(env)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(rec.gif_frames):
        Image.fromarray(np.asarray(f)).save(out_dir / f"{i:04d}.jpg", quality=90)
    vision.close()
    env.close()
    return {"seed": seed, "ok": bool(ok), "metrics": metrics, "frames": len(rec.gif_frames), "error": err}


def main():
    r1 = (HERE / "hero/round_1_skill.py").read_text()
    best = (HERE / "hero/best_skill.py").read_text()
    report = {}
    jobs = [("r1", r1, range(1000, 1008)), ("r2", best, range(2000, 2008))]
    for name, code, seeds in jobs:
        for s in seeds:
            res = episode(code, s, (480, 360), 1 / 25, "front", OUT / name / str(s))
            report[f"{name}/{s}"] = res
            print(name, res, flush=True)
    for name, code, s in (("hero_r1", r1, 1000), ("hero_r2", best, 2000)):
        for cam in ("front", "side"):
            res = episode(code, s, (1280, 960), 1 / 25, cam, OUT / name / cam)
            report[f"{name}/{cam}"] = res
            print(name, cam, res, flush=True)
    (OUT / "report.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
