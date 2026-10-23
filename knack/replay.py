"""Render GIFs of skills for the demo video: one episode, or a grid of parallel layouts."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .recorder import Recorder
from .robot import SimRobot
from .safety import RobotHalt
from .sandbox import compile_skill
from .sim import SimEnv
from .tasks import get_task


def record_episode(code: str, task_id: str, seed: int, size=(240, 180), every: float = 0.1, camera: str = "front",
                   realism: str = "sim"):
    from .sim import REALISM

    task = get_task(task_id)
    env = SimEnv(task, seed, render_size=size, realism=realism)
    robot = SimRobot(env, max_time=task.max_time, obs_noise=REALISM[realism]["pos_noise"], yaw_noise=REALISM[realism]["yaw_noise"])
    tmp = Path(".knack_tmp") / f"replay_{task_id}_{seed}"
    rec = Recorder(env, tmp, live_every=0.0, gif_every=every, live_camera=camera, gif_size=size)
    err = None
    try:
        compile_skill(code)(robot)
    except (Exception, RobotHalt) as e:
        err = f"{type(e).__name__}: {e}"
    env.step_seconds(0.5)
    frame = env.render(camera, size)
    if frame is not None:
        rec.gif_frames.append(frame)
    ok, _ = task.success(env)
    env.close()
    return rec.gif_frames, ok, err


def _label(img: np.ndarray, text: str, color) -> Image.Image:
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, 14], fill=(11, 14, 18))
    d.text((4, 2), text, fill=color)
    return im


def grid_gif(code: str, task_id: str, seeds: list, out: str, cols: int | None = None, size=(240, 180), fps: int = 10,
             realism: str = "sim") -> dict:
    eps = [record_episode(code, task_id, s, size=size, realism=realism) for s in seeds]
    n = len(eps)
    cols = cols or int(math.ceil(math.sqrt(n)))
    rows = int(math.ceil(n / cols))
    T = max(len(f) for f, _, _ in eps) if eps else 0
    W, H = size
    frames = []
    for t in range(T):
        canvas = Image.new("RGB", (cols * W, rows * H), (11, 14, 18))
        for i, ((fr, ok, _), seed) in enumerate(zip(eps, seeds)):
            if not fr:
                continue
            img = fr[min(t, len(fr) - 1)]
            done = t >= len(fr) - 1
            color = ((198, 255, 61) if ok else (255, 93, 61)) if done else (200, 205, 212)
            tag = f"seed {seed}" + (("  SUCCESS" if ok else "  FAIL") if done else "")
            canvas.paste(_label(img, tag, color), ((i % cols) * W, (i // cols) * H))
        frames.append(canvas)
    if frames:
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0)
    return {"out": out, "episodes": n, "success": sum(ok for _, ok, _ in eps), "frames": len(frames),
            "errors": [e for _, _, e in eps if e]}


def compare_gif(first_code: str, best_code: str, task_id: str, seeds: list, out: str, best_round: int | None = None,
                size=(240, 180), fps: int = 10, realism: str = "sim") -> dict:
    """Two rows on the same layouts: the first version (before any practice) and the practised version."""
    rows = [("FIRST TRY (round 1)", [record_episode(first_code, task_id, s, size=size, realism=realism) for s in seeds]),
            (f"AFTER PRACTICE (round {best_round})" if best_round else "AFTER PRACTICE",
             [record_episode(best_code, task_id, s, size=size, realism=realism) for s in seeds])]
    W, H = size
    band = 18
    T = max(len(f) for _, eps in rows for f, _, _ in eps)
    frames = []
    for t in range(T):
        canvas = Image.new("RGB", (len(seeds) * W, 2 * (H + band)), (11, 14, 18))
        d = ImageDraw.Draw(canvas)
        for r, (title, eps) in enumerate(rows):
            y0 = r * (H + band)
            k = sum(ok for _, ok, _ in eps)
            d.text((6, y0 + 3), f"{title}   {k}/{len(eps)} succeeded", fill=(198, 255, 61) if r else (200, 205, 212))
            for i, (fr, ok, _) in enumerate(eps):
                if not fr:
                    continue
                img = fr[min(t, len(fr) - 1)]
                done = t >= len(fr) - 1
                color = ((198, 255, 61) if ok else (255, 93, 61)) if done else (200, 205, 212)
                tag = ("SUCCESS" if ok else "FAIL") if done else ""
                canvas.paste(_label(img, tag, color), (i * W, y0 + band))
        frames.append(canvas)
    if frames:
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0)
        frames[-1].save(str(Path(out).with_suffix(".png")))
    return {"out": out, "first": sum(ok for _, ok, _ in rows[0][1]), "practised": sum(ok for _, ok, _ in rows[1][1]),
            "n": len(seeds), "frames": len(frames)}
