"""The robot API that AI-written skills program against.

Skills receive a `robot` object and may only call the public methods below.
The same API is exposed as MCP tools (knack.mcp_server) and implemented for
the real SO-101 (knack.real.so101). API_DOC is the single source of truth that
goes into the coding agent's prompt.
"""
from __future__ import annotations

import math

import numpy as np

from .kinematics import HOME_TCP, IKError, fk, ik
from .safety import EpisodeTimeout, RobotHalt, SafetyShield, SafetyViolation
from .sim import CTRL_DT, GRIP_CLOSED, GRIP_OPEN, SimEnv

API_DOC = """\
Robot API (all units metres / radians, world frame: x forward from the robot base,
y to the robot's left, z up, table surface at z = 0; the base is at x=0, y=0):

robot.observe() -> dict
    Snapshot of the scene from the robot's perception (positions have ~2 mm noise):
    {"time": s,
     "gripper": {"pos": [x, y, z], "yaw": rad, "opening": m, "holding": name or None},
     "objects": {name: {"pos": [x, y, z], "yaw": rad, "shape": "cube"|"puck",
                        "size": [...], "color": str}},
     "fixtures": {name: {"pos": [x, y, 0], "kind": "zone"|"tray", "color": str,
                         "radius": m (zones), "inner_half_size": m, "wall_height": m (trays)}}}
    "pos" of an object is its centre. Cube yaw is reported in [-pi/4, pi/4) (90 deg symmetry).

robot.get_pose(name) -> {"pos": [x, y, z], "yaw": rad}
    Pose of one object or fixture (same noise as observe()).

robot.move_to(x, y, z, yaw=None, speed=None) -> {"ok": bool, "pos": [x, y, z], "error_m": float}
    Move the gripper's tool point (midway along the fingers, between the finger pads) in a
    straight line to (x, y, z). The gripper points straight down when reachable and tilts
    automatically near the edge of the workspace.
    yaw: world angle of the fingers' closing direction. Pass an object's yaw to line the
    fingers up with its faces. None keeps the natural orientation.
    speed: m/s, default 0.15, capped at 0.30 by the safety layer.
    The fingertips reach 1.25 cm below the tool point. A cube resting on the table has its
    centre at z = 0.015, so z = 0.015 puts the finger pads around its middle.
    Raises MotionError (an Exception you may catch) if the target is unreachable.
    "ok" is False if the gripper was blocked before reaching the target.

robot.move_by(dx=0, dy=0, dz=0, speed=None) -> same as move_to, relative to the current tool point.

robot.grasp() -> bool
    Close the fingers (max opening 5 cm). Returns True if an object is held between them.

robot.release() -> None
    Open the fingers fully (5 cm gap).

robot.holding() -> name or None
robot.home() -> None              Move to a safe pose above the table.
robot.wait(seconds) -> None       Let time pass (max 5 s per call).
robot.log(*values) -> None        Write a debug note into the episode trace.

Safety layer (not negotiable): the tool point must stay inside x in [0.04, 0.32],
y in [-0.26, 0.26], z in [0.014, 0.26]. Targets up to 2 cm outside are clamped; further
out halts the skill. Pressing the gripper into the table with more than 30 N halts the
skill. Halts cannot be caught. Each episode has a time budget (simulated seconds).
Reachable band: roughly 0.10-0.23 m horizontal distance from the base at table height,
less when the tool point is high.
"""


class MotionError(Exception):
    """Raised for unreachable or invalid motion requests. Skills may catch it."""


def _r(v, n=4):
    if isinstance(v, (list, tuple, np.ndarray)):
        return [round(float(x), n) for x in v]
    return round(float(v), n)


def _wrap_quarter(yaw: float) -> float:
    return (yaw + math.pi / 4) % (math.pi / 2) - math.pi / 4


class SimRobot:
    """Robot API bound to a SimEnv. All internals are underscored so skills can't reach them."""

    def __init__(self, env: SimEnv, shield: SafetyShield | None = None, *, max_time: float = 45.0, obs_noise: float = 0.002, trace_limit: int = 400):
        self._env = env
        self._g = env.geometry
        self._shield = shield or SafetyShield(geometry=env.geometry)
        self._shield._clock = lambda: env.time
        self._max_time = float(max_time)
        self._obs_noise = float(obs_noise)
        self._noise_rng = np.random.default_rng(env.seed + 7_000_003)
        self._trace: list[dict] = []
        self._trace_limit = trace_limit
        self._halted: str | None = None
        self._calls = 0
        env.add_tick_callback(self._on_tick)

    # ------------------------------------------------------------------ internals
    def _log_call(self, call: str, result=None, error: str | None = None):
        self._calls += 1
        if len(self._trace) < self._trace_limit:
            e = {"t": round(self._env.time, 2), "call": call}
            if result is not None:
                e["result"] = result
            if error:
                e["error"] = error
            self._trace.append(e)
        elif len(self._trace) == self._trace_limit:
            self._trace.append({"t": round(self._env.time, 2), "call": "...", "result": "trace truncated"})

    def _check_alive(self):
        if self._halted:
            raise RobotHalt(f"robot is halted: {self._halted}")

    def _on_tick(self, env):
        if self._halted:
            return
        if env.time > self._max_time:
            self._halted = f"time budget of {self._max_time:.0f} s exceeded"
            raise EpisodeTimeout(self._halted)
        try:
            self._shield.check_table_force(env.gripper_table_force())
        except SafetyViolation as e:
            self._halted = str(e)
            env.set_arm_target(env.arm_q())  # freeze
            raise

    def _noisy(self, p):
        p = np.asarray(p, dtype=float)
        if self._obs_noise > 0:
            p = p + self._noise_rng.normal(0.0, self._obs_noise, size=p.shape)
        return p

    def _object_entry(self, name: str, noisy: bool = True) -> dict:
        env = self._env
        spec = env.obj_spec[name]
        pos, yaw = env.object_pose(name)
        if noisy:
            pos = self._noisy(pos)
            yaw = yaw + (self._noise_rng.normal(0.0, 0.02) if self._obs_noise > 0 else 0.0)
        if spec.shape == "cube":
            yaw = _wrap_quarter(yaw)
            size = [spec.size[0]] * 3
        else:
            size = {"radius": spec.size[0], "height": spec.size[1]}
        return {"pos": _r(pos), "yaw": _r(yaw), "shape": spec.shape, "size": size, "color": spec.color}

    def _fixture_entry(self, name: str, noisy: bool = True) -> dict:
        env = self._env
        f = env.fixture_spec[name]
        pos = env.fixture_pos(name)
        if noisy:
            pos = pos + np.array([*self._noise_rng.normal(0.0, self._obs_noise, 2), 0.0]) if self._obs_noise > 0 else pos
        e = {"pos": _r(pos), "kind": f.kind, "color": f.color}
        if f.kind == "zone":
            e["radius"] = f.radius
        else:
            from .tasks import TRAY_INNER, TRAY_WALL_H

            e["inner_half_size"] = TRAY_INNER
            e["wall_height"] = TRAY_WALL_H
        return e

    def snapshot(self, noisy: bool = False) -> dict:
        """Full scene state (used by the harness, not exposed to skills by name)."""
        env = self._env
        q = env.arm_q()
        k = fk(q, self._g)
        return {
            "time": round(env.time, 2),
            "gripper": {
                "pos": _r(env.tcp()),
                "yaw": _r(k["yaw"]),
                "opening": _r(env.finger_opening()),
                "holding": env.held_object(),
            },
            "objects": {n: self._object_entry(n, noisy) for n in env.obj_spec},
            "fixtures": {n: self._fixture_entry(n, noisy) for n in env.fixture_spec},
        }

    @property
    def trace(self) -> list:
        return self._trace

    @property
    def halted(self):
        return self._halted

    # ------------------------------------------------------------------ public API
    def observe(self) -> dict:
        self._check_alive()
        obs = self.snapshot(noisy=True)
        self._log_call("observe()", "ok")
        return obs

    def get_pose(self, name: str) -> dict:
        self._check_alive()
        env = self._env
        if name in env.obj_spec:
            e = self._object_entry(name)
            out = {"pos": e["pos"], "yaw": e["yaw"]}
        elif name in env.fixture_spec:
            e = self._fixture_entry(name)
            out = {"pos": e["pos"], "yaw": 0.0}
        else:
            known = list(env.obj_spec) + list(env.fixture_spec)
            self._log_call(f"get_pose({name!r})", error="unknown name")
            raise KeyError(f"unknown object or fixture {name!r}; known: {known}")
        self._log_call(f"get_pose({name!r})", out)
        return out

    def move_to(self, x, y, z, yaw=None, speed=None) -> dict:
        self._check_alive()
        call = f"move_to({_fmt(x)}, {_fmt(y)}, {_fmt(z)}" + (f", yaw={_fmt(yaw)}" if yaw is not None else "") + (f", speed={_fmt(speed)}" if speed is not None else "") + ")"
        try:
            target = np.array([float(x), float(y), float(z)])
            yaw_f = None if yaw is None else float(yaw)
        except (TypeError, ValueError):
            self._log_call(call, error="non-numeric argument")
            raise MotionError("move_to expects numbers for x, y, z (and yaw)") from None
        try:
            target = self._shield.filter_target(target)
        except SafetyViolation as e:
            self._halted = str(e)
            self._log_call(call, error=f"SAFETY HALT: {e}")
            raise
        v = self._shield.filter_speed(speed)
        try:
            q_goal = ik(target, yaw_f, self._g)
        except IKError as e:
            self._log_call(call, error=f"MotionError: {e}")
            raise MotionError(str(e)) from None
        try:
            self._shield.check_joint_target(q_goal)
        except SafetyViolation as e:
            self._halted = str(e)
            self._log_call(call, error=f"SAFETY HALT: {e}")
            raise
        result = self._execute_line(target, q_goal, yaw_f, v)
        self._log_call(call, result)
        return result

    def move_by(self, dx=0.0, dy=0.0, dz=0.0, speed=None) -> dict:
        self._check_alive()
        p = self._env.tcp()
        q = self._env.arm_q()
        yaw = fk(q, self._g)["yaw"]
        try:
            return self.move_to(p[0] + float(dx), p[1] + float(dy), p[2] + float(dz), yaw=yaw, speed=speed)
        except (TypeError, ValueError):
            raise MotionError("move_by expects numbers") from None

    def _execute_line(self, target, q_goal, yaw, speed) -> dict:
        env = self._env
        start = env.tcp()
        q_start = env.arm_target()
        psi0 = fk(q_start, self._g)["pitch"]
        psi1 = fk(q_goal, self._g)["pitch"]
        dist = float(np.linalg.norm(target - start))
        dang = float(np.max(np.abs(q_goal - q_start)))
        T = max(dist / speed, dang / (0.8 * self._shield.limits.max_joint_speed), 0.15)
        n = max(1, int(math.ceil(T / CTRL_DT)))
        q_prev = q_start
        for i in range(1, n + 1):
            s = i / n
            s = s * s * (3 - 2 * s)  # smoothstep
            p = start + (target - start) * s
            psi = psi0 + (psi1 - psi0) * s
            try:
                q = ik(p, yaw, self._g, pitch=psi)
            except IKError:
                q = q_start + (q_goal - q_start) * s
            q[4] = q_start[4] + (q_goal[4] - q_start[4]) * s
            q = self._shield.limit_joint_step(q_prev, q, CTRL_DT)
            env.set_arm_target(q)
            env.tick()
            q_prev = q
        # catch up on any joint-speed-limited lag, then settle
        for _ in range(int(1.5 / CTRL_DT)):
            q = self._shield.limit_joint_step(q_prev, q_goal, CTRL_DT)
            env.set_arm_target(q)
            q_prev = q
            env.tick()
            if np.allclose(q, q_goal) and np.linalg.norm(env.tcp() - target) < 0.002 and np.max(np.abs(env.arm_qvel())) < 0.05:
                break
        err = float(np.linalg.norm(env.tcp() - target))
        out = {"ok": err < 0.01, "pos": _r(env.tcp()), "error_m": round(err, 4)}
        if err >= 0.01:
            out["note"] = "stopped short of the target (blocked by contact or joint limit)"
        return out

    def grasp(self) -> bool:
        self._check_alive()
        self._env.set_grip(GRIP_CLOSED)
        for _ in range(int(0.5 / CTRL_DT)):
            self._env.tick()
        held = self._env.held_object()
        self._log_call("grasp()", {"holding": held, "opening": _r(self._env.finger_opening())})
        return held is not None

    def release(self) -> None:
        self._check_alive()
        self._env.set_grip(GRIP_OPEN)
        for _ in range(int(0.4 / CTRL_DT)):
            self._env.tick()
        self._log_call("release()", "open")

    def holding(self):
        self._check_alive()
        h = self._env.held_object()
        self._log_call("holding()", h)
        return h

    def home(self) -> None:
        self._check_alive()
        self.move_to(*HOME_TCP)

    def wait(self, seconds=0.5) -> None:
        self._check_alive()
        try:
            s = min(max(float(seconds), 0.0), 5.0)
        except (TypeError, ValueError):
            s = 0.5
        for _ in range(int(round(s / CTRL_DT))):
            self._env.tick()
        self._log_call(f"wait({s:.2f})", "ok")

    def log(self, *values) -> None:
        msg = " ".join(str(v) for v in values)[:300]
        self._log_call("log", msg)


def _fmt(v) -> str:
    try:
        return f"{float(v):.3f}"
    except (TypeError, ValueError):
        return repr(v)[:20]


PUBLIC_METHODS = ("observe", "get_pose", "move_to", "move_by", "grasp", "release", "holding", "home", "wait", "log")

__all__ = ["SimRobot", "MotionError", "RobotHalt", "SafetyViolation", "EpisodeTimeout", "API_DOC", "PUBLIC_METHODS"]
