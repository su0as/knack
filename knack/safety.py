"""Deterministic safety shield that sits under every AI-written skill.

The language model never talks to the motors. Every command goes through this
layer, which is plain Python with fixed limits: workspace box, joint limits,
Cartesian and joint speed caps, elbow height, and a gripper-table force limit
(sim only). It is shared by the simulator and the real-arm backend.

Small violations (within `clamp_tolerance`) are clamped and logged. Larger ones
halt the skill with SafetyViolation, which skills cannot catch.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .kinematics import SIM_ARM, ArmGeometry, fk, within_limits


class RobotHalt(BaseException):
    """Stops the skill. Derives from BaseException so `except Exception` cannot swallow it."""


class SafetyViolation(RobotHalt):
    pass


class EpisodeTimeout(RobotHalt):
    pass


@dataclass
class Limits:
    x: tuple = (0.04, 0.32)
    y: tuple = (-0.26, 0.26)
    z: tuple = (0.014, 0.26)
    clamp_tolerance: float = 0.02
    default_speed: float = 0.15  # m/s
    max_speed: float = 0.30  # m/s
    max_joint_speed: float = 2.5  # rad/s
    max_table_force: float = 30.0  # N, gripper pressing on the table
    min_elbow_z: float = 0.03
    min_wrist_z: float = 0.03

    def to_dict(self) -> dict:
        return asdict(self)


class SafetyShield:
    def __init__(self, limits: Limits | None = None, geometry: ArmGeometry = SIM_ARM, clock=None):
        self.limits = limits or Limits()
        self.geometry = geometry
        self.events: list[dict] = []
        self._clock = clock or (lambda: 0.0)

    def _event(self, kind: str, detail: str, action: str):
        if len(self.events) < 200:
            self.events.append({"t": round(float(self._clock()), 2), "kind": kind, "action": action, "detail": detail})

    # ---- Cartesian target ----
    def filter_target(self, p) -> np.ndarray:
        p = np.asarray(p, dtype=float).copy()
        if not np.all(np.isfinite(p)):
            self._event("target", f"non-finite target {p.tolist()}", "halt")
            raise SafetyViolation(f"non-finite target {p.tolist()}")
        L = self.limits
        for i, (axis, (lo, hi)) in enumerate(zip("xyz", (L.x, L.y, L.z))):
            v = p[i]
            if v < lo or v > hi:
                over = (lo - v) if v < lo else (v - hi)
                if over > L.clamp_tolerance:
                    self._event("workspace", f"{axis}={v:.3f} outside [{lo}, {hi}] by {over:.3f} m", "halt")
                    raise SafetyViolation(
                        f"target {axis}={v:.3f} m is outside the safe workspace [{lo}, {hi}] by {over:.3f} m"
                    )
                p[i] = min(max(v, lo), hi)
                self._event("workspace", f"{axis}={v:.3f} clamped to {p[i]:.3f}", "clamp")
        return p

    def filter_speed(self, speed) -> float:
        L = self.limits
        if speed is None:
            return L.default_speed
        try:
            s = float(speed)
        except (TypeError, ValueError):
            return L.default_speed
        if not np.isfinite(s) or s <= 0:
            return L.default_speed
        if s > L.max_speed:
            self._event("speed", f"requested {s:.2f} m/s capped at {L.max_speed}", "clamp")
            return L.max_speed
        return s

    # ---- joint space ----
    def check_joint_target(self, q):
        if not within_limits(q, self.geometry):
            self._event("joint_limits", f"q={np.round(q, 3).tolist()}", "halt")
            raise SafetyViolation("joint target outside joint limits")
        k = fk(q, self.geometry)
        if k["elbow"][2] < self.limits.min_elbow_z or k["wrist"][2] < self.limits.min_wrist_z:
            self._event("clearance", "elbow or wrist too close to the table", "halt")
            raise SafetyViolation("elbow or wrist would come too close to the table")

    def limit_joint_step(self, q_prev, q_next, dt: float) -> np.ndarray:
        q_prev = np.asarray(q_prev, dtype=float)
        q_next = np.asarray(q_next, dtype=float)
        max_step = self.limits.max_joint_speed * dt
        dq = np.clip(q_next - q_prev, -max_step, max_step)
        return q_prev + dq

    # ---- contact ----
    def check_table_force(self, force: float):
        if force > self.limits.max_table_force:
            self._event("force", f"gripper pressed on the table with {force:.1f} N", "halt")
            raise SafetyViolation(
                f"gripper pressed into the table with {force:.1f} N (limit {self.limits.max_table_force} N)"
            )

    def summary(self) -> dict:
        out = {"clamp": 0, "halt": 0}
        for e in self.events:
            out[e["action"]] = out.get(e["action"], 0) + 1
        return out
