"""python -m knack.real run SKILL.py --task lift [--port COM5] [--camera 0] [--config so101_config.json] [--dry-run]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m knack.real")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run", help="run a skill file on the real arm")
    p.add_argument("skill")
    p.add_argument("--task", required=True)
    p.add_argument("--port")
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--config")
    p.add_argument("--calib", default="camera_calib.json")
    p.add_argument("--dry-run", action="store_true")
    sub.add_parser("config", help="print the default config to edit")
    a = ap.parse_args(argv)
    from .so101 import DEFAULT_CONFIG, SO101Robot, load_config

    if a.cmd == "config":
        print(json.dumps(DEFAULT_CONFIG, indent=1))
        return 0
    from ..sandbox import compile_skill
    from ..tasks import get_task

    cfg = load_config(a.config)
    if a.port:
        cfg["port"] = a.port
    task = get_task(a.task)
    vision = None
    if not a.dry_run:
        from .vision import OverheadVision

        vision = OverheadVision(a.camera, a.calib)
    robot = SO101Robot(cfg, task, vision=vision, dry_run=a.dry_run)
    try:
        fn = compile_skill(Path(a.skill).read_text(encoding="utf-8"), printer=print)
        ret = fn(robot)
        print("skill returned", ret)
    except BaseException as e:
        print(f"stopped: {type(e).__name__}: {e}")
    finally:
        robot.close()
        print(json.dumps(robot.trace[-20:], indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
