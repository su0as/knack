"""Run a Knack skill on a real SO-101 arm (EXPERIMENTAL, not yet tested on hardware).

Same public API as the simulator robot, same IK and the same SafetyShield, so a
skill learned in simulation runs unchanged with no cloud calls:

    python -m knack.real run runs/<run>/best_skill.py --task lift --port COM5 --camera 0
    python -m knack.real run skill.py --task lift --dry-run      # no hardware, prints joint commands

Before the first real run:
  1. Calibrate the arm with LeRobot (lerobot-calibrate) and set use_degrees.
  2. Measure the link lengths and fill so101_config.json (see DEFAULT_CONFIG): the sim arm is
     only SO-101-proportioned, the real one must use real numbers.
  3. Fix sign/offset per joint so that knack's zero pose (arm straight out, horizontal,
     gripper fingers horizontal) maps to the right LeRobot degrees. Test with --dry-run, then
     with the arm lifted off the table and a hand on the e-stop.
  4. Calibrate the overhead camera: knack.real.vision.calibrate_homography().
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np

from ..kinematics import HOME_TCP, ArmGeometry, IKError, fk, ik
from ..robot import API_DOC, MotionError, _r
from ..safety import Limits, RobotHalt, SafetyShield, SafetyViolation

JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")

DEFAULT_CONFIG = {
    "port": "COM5",
    "robot_id": "knack_follower",
    "geometry": {"shoulder_height": 0.1, "l1": 0.116, "l2": 0.135, "l3": 0.115, "base": [0.0, 0.0]},
    "joint_sign": {"shoulder_pan": 1, "shoulder_lift": -1, "elbow_flex": 1, "wrist_flex": 1, "wrist_roll": 1},
    "joint_offset_deg": {"shoulder_pan": 0, "shoulder_lift": 90, "elbow_flex": -90, "wrist_flex": 0, "wrist_roll": 0},
    "gripper_open": 60.0,
    "gripper_closed": 0.0,
    "gripper_holding_threshold": 6.0,
    "control_hz": 30,
    "max_speed": 0.08,
    "_note": "UNVERIFIED defaults. Measure and fix before running on hardware.",
}


def load_config(path: str | None) -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if path and Path(path).exists():
        cfg.update(json.loads(Path(path).read_text(encoding="utf-8")))
    return cfg


class _DryArm:
    """Stands in for the LeRobot follower: records commands, echoes positions."""

    def __init__(self):
        self.pos = {f"{j}.pos": 0.0 for j in JOINTS} | {"gripper.pos": 50.0}
        self.log = []

    def connect(self):
        pass

    def get_observation(self):
        return dict(self.pos)

    def send_action(self, action: dict):
        self.pos.update(action)
        self.log.append(action)
        return action

    def disconnect(self):
        pass


def _lerobot_follower(port: str, robot_id: str):
    try:
        from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
    except ImportError:
        try:
            from lerobot.common.robots.so101_follower import SO101Follower, SO101FollowerConfig
        except ImportError as e:
            raise RuntimeError("LeRobot with SO-101 support is not installed: pip install 'knack[real]'") from e
    try:
        cfg = SO101FollowerConfig(port=port, id=robot_id, use_degrees=True)
    except TypeError:
        cfg = SO101FollowerConfig(port=port, id=robot_id)
    return SO101Follower(cfg)


class SO101Robot:
    def __init__(self, cfg: dict, task, vision=None, dry_run: bool = False, max_time: float = 120.0):
        g = cfg["geometry"]
        self._cfg = cfg
        self._g = ArmGeometry(base=tuple(g["base"]), shoulder_height=g["shoulder_height"], l1=g["l1"], l2=g["l2"], l3=g["l3"])
        self._shield = SafetyShield(Limits(max_speed=cfg["max_speed"], default_speed=min(0.06, cfg["max_speed"])), self._g,
                                    clock=lambda: time.time() - self._t0)
        self._arm = _DryArm() if dry_run else _lerobot_follower(cfg["port"], cfg["robot_id"])
        self._arm.connect()
        self._vision = vision
        self._task = task
        self._dry = dry_run
        self._t0 = time.time()
        self._max_time = max_time
        self._trace = []
        self._q = self._read_q()
        self._grip = cfg["gripper_open"]

    # ---- joint mapping ----
    def _to_deg(self, q) -> dict:
        s, o = self._cfg["joint_sign"], self._cfg["joint_offset_deg"]
        return {f"{j}.pos": float(s[j] * math.degrees(q[i]) + o[j]) for i, j in enumerate(JOINTS)}

    def _read_q(self) -> np.ndarray:
        obs = self._arm.get_observation()
        s, o = self._cfg["joint_sign"], self._cfg["joint_offset_deg"]
        return np.array([math.radians((obs[f"{j}.pos"] - o[j]) / s[j]) for j in JOINTS])

    def _send(self, q):
        self._arm.send_action({**self._to_deg(q), "gripper.pos": self._grip})
        self._q = np.asarray(q, dtype=float)

    def _log(self, call, result=None, error=None):
        e = {"t": round(time.time() - self._t0, 2), "call": call}
        if result is not None:
            e["result"] = result
        if error:
            e["error"] = error
        self._trace.append(e)

    def _check_time(self):
        if time.time() - self._t0 > self._max_time:
            raise RobotHalt("time budget exceeded")

    # ---- public API (mirrors SimRobot) ----
    def observe(self) -> dict:
        objs = self._vision.detect(self._task) if self._vision else {}
        k = fk(self._q, self._g)
        return {"time": round(time.time() - self._t0, 2),
                "gripper": {"pos": _r(k["tcp"]), "yaw": _r(k["yaw"]), "opening": None, "holding": None},
                "objects": objs.get("objects", {}), "fixtures": objs.get("fixtures", {})}

    def get_pose(self, name):
        o = self.observe()
        for group in ("objects", "fixtures"):
            if name in o[group]:
                return {"pos": o[group][name]["pos"], "yaw": o[group][name].get("yaw", 0.0)}
        raise KeyError(f"{name} not detected by the camera")

    def move_to(self, x, y, z, yaw=None, speed=None):
        self._check_time()
        target = self._shield.filter_target(np.array([float(x), float(y), float(z)]))
        v = self._shield.filter_speed(speed)
        try:
            q_goal = ik(target, yaw, self._g)
        except IKError as e:
            raise MotionError(str(e)) from None
        self._shield.check_joint_target(q_goal)
        start = fk(self._q, self._g)["tcp"]
        dt = 1.0 / self._cfg["control_hz"]
        dist = float(np.linalg.norm(target - start))
        n = max(1, int(math.ceil(max(dist / v, 0.3) / dt)))
        q_prev = self._q.copy()
        for i in range(1, n + 1):
            s = i / n
            s = s * s * (3 - 2 * s)
            try:
                q = ik(start + (target - start) * s, yaw, self._g)
            except IKError:
                q = q_prev + (q_goal - q_prev) * s
            q = self._shield.limit_joint_step(q_prev, q, dt)
            self._shield.check_joint_target(q)
            self._send(q)
            q_prev = q
            time.sleep(0 if self._dry else dt)
        self._send(q_goal)
        out = {"ok": True, "pos": _r(fk(self._q, self._g)["tcp"]), "error_m": None}
        self._log(f"move_to({x:.3f}, {y:.3f}, {z:.3f})", out)
        return out

    def move_by(self, dx=0.0, dy=0.0, dz=0.0, speed=None):
        p = fk(self._q, self._g)["tcp"]
        return self.move_to(p[0] + dx, p[1] + dy, p[2] + dz, yaw=fk(self._q, self._g)["yaw"], speed=speed)

    def grasp(self) -> bool:
        self._grip = self._cfg["gripper_closed"]
        self._send(self._q)
        time.sleep(0 if self._dry else 0.8)
        pos = self._arm.get_observation().get("gripper.pos", 0.0)
        held = (pos - self._cfg["gripper_closed"]) > self._cfg["gripper_holding_threshold"] and not self._dry
        self._log("grasp()", {"gripper_pos": pos, "holding": held})
        return held

    def release(self):
        self._grip = self._cfg["gripper_open"]
        self._send(self._q)
        time.sleep(0 if self._dry else 0.6)
        self._log("release()", "open")

    def holding(self):
        pos = self._arm.get_observation().get("gripper.pos", 0.0)
        return "object" if (pos - self._cfg["gripper_closed"]) > self._cfg["gripper_holding_threshold"] else None

    def home(self):
        self.move_to(*HOME_TCP)

    def wait(self, seconds=0.5):
        time.sleep(0 if self._dry else min(max(float(seconds), 0), 5))

    def log(self, *values):
        self._log("log", " ".join(map(str, values))[:300])

    def close(self):
        try:
            self._arm.disconnect()
        except Exception:
            pass

    @property
    def trace(self):
        return self._trace


__all__ = ["SO101Robot", "load_config", "DEFAULT_CONFIG", "API_DOC", "SafetyViolation"]
