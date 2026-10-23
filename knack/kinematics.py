"""Kinematics for the Knack arm.

A 5-DoF SO-101-style arm (shoulder pan, shoulder lift, elbow flex, wrist flex,
wrist roll) with a parallel gripper. Pure numpy, no MuJoCo, so the same code
drives the simulator and the real-arm backend.

World frame: x forward from the robot base, y to the robot's left, z up,
table surface at z = 0. Units: metres and radians.

Planar convention: after the pan rotation, the three pitch joints move the arm
in a vertical plane. Angles are measured from the horizontal, positive = up.
The tool pitch psi = q_lift + q_elbow + q_wrist; psi = -pi/2 means the gripper
points straight down.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

JOINT_NAMES = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")


@dataclass(frozen=True)
class ArmGeometry:
    base: tuple = (0.0, 0.0)  # xy of the pan axis
    shoulder_height: float = 0.10  # z of the shoulder-lift axis
    l1: float = 0.116  # shoulder lift -> elbow
    l2: float = 0.135  # elbow -> wrist flex
    l3: float = 0.115  # wrist flex -> TCP (point between the finger pads)
    joint_limits: tuple = (
        (-2.0, 2.0),  # shoulder_pan
        (-0.3, 2.2),  # shoulder_lift
        (-2.7, 0.2),  # elbow_flex
        (-2.2, 2.2),  # wrist_flex
        (-3.0, 3.0),  # wrist_roll
    )
    finger_travel: float = 0.025  # per finger; full opening = 2 x travel
    min_elbow_z: float = 0.03

    @property
    def max_reach(self) -> float:
        return self.l1 + self.l2


# Proportioned like the SO-101 but simplified (primitive shapes, zero offsets).
SIM_ARM = ArmGeometry()

HOME_TCP = (0.16, 0.0, 0.14)


class IKError(ValueError):
    """Target pose cannot be reached by the arm."""


def wrap_pi(a: float) -> float:
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def wrap_half_pi(a: float) -> float:
    """Wrap to [-pi/2, pi/2). A parallel gripper is symmetric under a 180 deg roll."""
    return (a + math.pi / 2.0) % math.pi - math.pi / 2.0


def roll_for_yaw(pan: float, yaw: float | None) -> float:
    """Wrist roll that makes the finger closing axis point along world `yaw`.

    Derived for a downward-pointing tool: closing-axis yaw = pan + pi/2 - roll.
    """
    if yaw is None:
        return 0.0
    return wrap_half_pi(pan + math.pi / 2.0 - yaw)


def fk(q, g: ArmGeometry = SIM_ARM) -> dict:
    """Forward kinematics. Returns TCP, wrist and elbow positions, tool pitch and gripper yaw."""
    pan, q1, q2, q3, roll = (float(v) for v in q)
    r_e = g.l1 * math.cos(q1)
    z_e = g.shoulder_height + g.l1 * math.sin(q1)
    r_w = r_e + g.l2 * math.cos(q1 + q2)
    z_w = z_e + g.l2 * math.sin(q1 + q2)
    psi = q1 + q2 + q3
    r_t = r_w + g.l3 * math.cos(psi)
    z_t = z_w + g.l3 * math.sin(psi)
    c, s = math.cos(pan), math.sin(pan)
    bx, by = g.base

    def xyz(r, z):
        return np.array([bx + r * c, by + r * s, z])

    return {
        "tcp": xyz(r_t, z_t),
        "wrist": xyz(r_w, z_w),
        "elbow": xyz(r_e, z_e),
        "pitch": psi,
        "yaw": wrap_pi(pan + math.pi / 2.0 - roll),
    }


def _pitch_candidates() -> list[float]:
    base = -math.pi / 2.0
    out = [base]
    for k in range(1, 9):
        out.append(base + 0.1 * k)  # tilt the fingertips outward (more reach)
        out.append(base - 0.1 * k)  # tilt the fingertips inward (closer targets)
    return out


PITCH_CANDIDATES = _pitch_candidates()


def within_limits(q, g: ArmGeometry = SIM_ARM, margin: float = 1e-6) -> bool:
    return all(lo - margin <= float(v) <= hi + margin for v, (lo, hi) in zip(q, g.joint_limits))


def ik(target, yaw: float | None = None, g: ArmGeometry = SIM_ARM, pitch: float | None = None) -> np.ndarray:
    """Analytic IK (elbow-up). Prefers a straight-down gripper, tilts if needed.

    Raises IKError with a human-readable reason if no candidate pitch works.
    """
    x, y, z = (float(v) for v in target)
    dx, dy = x - g.base[0], y - g.base[1]
    r = math.hypot(dx, dy)
    if r < 0.03:
        raise IKError(f"target ({x:.3f}, {y:.3f}, {z:.3f}) is too close to the robot base (r={r:.3f} m)")
    pan = math.atan2(dy, dx)
    roll = roll_for_yaw(pan, yaw)
    pitches = [pitch] if pitch is not None else PITCH_CANDIDATES
    best_reason = "out of reach"
    for psi in pitches:
        rw = r - g.l3 * math.cos(psi)
        zw = z - g.l3 * math.sin(psi) - g.shoulder_height
        d2 = rw * rw + zw * zw
        c2 = (d2 - g.l1 ** 2 - g.l2 ** 2) / (2.0 * g.l1 * g.l2)
        if c2 > 1.0 or c2 < -1.0:
            best_reason = (
                f"wrist point is {math.sqrt(d2):.3f} m from the shoulder; the arm reaches "
                f"{abs(g.l1 - g.l2):.3f}..{g.max_reach:.3f} m"
            )
            continue
        q2 = -math.acos(c2)
        q1 = math.atan2(zw, rw) - math.atan2(g.l2 * math.sin(q2), g.l1 + g.l2 * math.cos(q2))
        q3 = psi - q1 - q2
        q = np.array([pan, q1, q2, q3, roll])
        if not within_limits(q, g):
            best_reason = "joint limits"
            continue
        if g.shoulder_height + g.l1 * math.sin(q1) < g.min_elbow_z:
            best_reason = "elbow would hit the table"
            continue
        return q
    raise IKError(
        f"target ({x:.3f}, {y:.3f}, {z:.3f}) unreachable ({best_reason}); horizontal distance from base "
        f"{r:.3f} m. Typical reachable band: 0.10-0.23 m from the base at table height."
    )


def reachable(target, g: ArmGeometry = SIM_ARM) -> bool:
    try:
        ik(target, None, g)
        return True
    except IKError:
        return False
