"""Task scenes and ground-truth success checks.

Each task is a tabletop scene (objects + fixtures) with a natural-language
instruction and a deterministic success predicate computed from simulator
state. The predicate is the ground truth (GT) reward; the coding agent only
sees it when the run uses reward="gt".
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

COLORS = {
    "red": (0.86, 0.20, 0.18, 1.0),
    "blue": (0.17, 0.38, 0.86, 1.0),
    "green": (0.18, 0.72, 0.32, 1.0),
    "yellow": (0.96, 0.78, 0.12, 1.0),
    "orange": (0.97, 0.50, 0.10, 1.0),
    "purple": (0.55, 0.30, 0.80, 1.0),
}

CUBE = 0.03  # edge length (m)
TRAY_INNER = 0.044  # inner half-size of a tray (m)
TRAY_WALL_H = 0.025


@dataclass
class ObjSpec:
    name: str
    shape: str  # "cube" | "puck"
    color: str
    size: tuple  # cube: (edge,); puck: (radius, height)
    mass: float = 0.03

    @property
    def footprint(self) -> float:
        if self.shape == "cube":
            return self.size[0] * 0.75
        return self.size[0] + 0.005

    @property
    def rest_z(self) -> float:
        return self.size[0] / 2 if self.shape == "cube" else self.size[1] / 2


@dataclass
class FixtureSpec:
    name: str
    kind: str  # "zone" | "tray"
    color: str
    radius: float = 0.035  # zone radius

    @property
    def footprint(self) -> float:
        return self.radius + 0.01 if self.kind == "zone" else 0.072


@dataclass
class Task:
    id: str
    title: str
    instruction: str
    objects: list = field(default_factory=list)
    fixtures: list = field(default_factory=list)
    max_time: float = 45.0
    r_range: tuple = (0.12, 0.20)
    theta_range: tuple = (-0.85, 0.85)
    difficulty: int = 1

    # ---------- layout ----------
    def sample_layout(self, rng: np.random.Generator) -> dict:
        """Random positions/yaws for fixtures then objects, with clearance."""
        for _attempt in range(2000):
            placed: dict[str, dict] = {}
            ok = True
            items = [(f.name, f.footprint, f) for f in self.fixtures] + [(o.name, o.footprint, o) for o in self.objects]
            for name, fp, spec in items:
                pose = self._sample_one(rng, name, fp, spec, placed)
                if pose is None:
                    ok = False
                    break
                placed[name] = pose
            if ok and self._layout_ok(placed):
                return placed
        raise RuntimeError(f"could not sample a layout for task {self.id}")

    def _sample_one(self, rng, name, fp, spec, placed):
        r_lo, r_hi = self.r_range
        if isinstance(spec, FixtureSpec) and spec.kind == "tray":
            r_lo, r_hi = max(r_lo, 0.135), min(r_hi, 0.185)
        for _ in range(200):
            r = rng.uniform(r_lo, r_hi)
            th = rng.uniform(*self.theta_range)
            x, y = r * math.cos(th), r * math.sin(th)
            if all(math.hypot(x - p["x"], y - p["y"]) > fp + p["fp"] + 0.012 for p in placed.values()):
                yaw = float(rng.uniform(-math.pi / 4, math.pi / 4)) if isinstance(spec, ObjSpec) else 0.0
                return {"x": float(x), "y": float(y), "yaw": yaw, "fp": fp}
        return None

    def _layout_ok(self, placed: dict) -> bool:
        return True

    # ---------- success ----------
    def success(self, env) -> tuple[bool, dict]:
        raise NotImplementedError

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "instruction": self.instruction,
            "difficulty": self.difficulty,
            "objects": [o.name for o in self.objects],
            "fixtures": [f.name for f in self.fixtures],
            "max_time": self.max_time,
        }


def _xy_dist(a, b) -> float:
    return float(math.hypot(a[0] - b[0], a[1] - b[1]))


def _in_tray(env, obj: str, tray: str) -> tuple[bool, dict]:
    p, _ = env.object_pose(obj)
    t = env.fixture_pos(tray)
    dx, dy = abs(p[0] - t[0]), abs(p[1] - t[1])
    inside = dx <= 0.035 and dy <= 0.035 and p[2] < 0.035
    held = env.is_held(obj)
    return inside and not held, {f"{obj}_tray_dx": round(dx, 4), f"{obj}_tray_dy": round(dy, 4), f"{obj}_z": round(float(p[2]), 4), f"{obj}_held": held}


class LiftTask(Task):
    def success(self, env):
        p, _ = env.object_pose("red_cube")
        need = CUBE / 2 + 0.05
        return bool(p[2] >= need), {"red_cube_z": round(float(p[2]), 4), "required_z": need}


class PlaceTask(Task):
    def success(self, env):
        p, _ = env.object_pose("blue_cube")
        t = env.fixture_pos("target")
        d = _xy_dist(p, t)
        held = env.is_held("blue_cube")
        ok = d <= 0.03 and p[2] < 0.025 and not held
        return ok, {"blue_cube_to_target_xy": round(d, 4), "tolerance": 0.03, "blue_cube_z": round(float(p[2]), 4), "held": held}


class PushTask(Task):
    def _layout_ok(self, placed):
        d = math.hypot(placed["puck"]["x"] - placed["target"]["x"], placed["puck"]["y"] - placed["target"]["y"])
        return 0.07 <= d <= 0.12

    def success(self, env):
        p, _ = env.object_pose("puck")
        t = env.fixture_pos("target")
        d = _xy_dist(p, t)
        upright = env.object_tilt("puck") < 0.3
        ok = d <= 0.035 and upright and p[2] < 0.02
        return ok, {"puck_to_target_xy": round(d, 4), "tolerance": 0.035, "upright": upright}


class StackTask(Task):
    def success(self, env):
        r, _ = env.object_pose("red_cube")
        b, _ = env.object_pose("blue_cube")
        dxy = _xy_dist(r, b)
        dz = float(r[2] - b[2])
        held = env.is_held("red_cube")
        ok = dxy <= 0.016 and 0.024 <= dz <= 0.036 and b[2] < 0.02 and not held
        return ok, {"xy_offset": round(dxy, 4), "z_gap": round(dz, 4), "red_held": held, "blue_z": round(float(b[2]), 4)}


class TrayTask(Task):
    def success(self, env):
        return _in_tray(env, "yellow_cube", "tray")


class SortTask(Task):
    def success(self, env):
        ok_r, m_r = _in_tray(env, "red_cube", "red_tray")
        ok_b, m_b = _in_tray(env, "blue_cube", "blue_tray")
        m = {**m_r, **m_b, "red_ok": ok_r, "blue_ok": ok_b}
        return ok_r and ok_b, m


def _cube(name, color, mass=0.03):
    return ObjSpec(name, "cube", color, (CUBE,), mass)


TASKS: dict[str, Task] = {}


def _register(t: Task) -> Task:
    TASKS[t.id] = t
    return t


_register(LiftTask(
    id="lift",
    title="Lift",
    instruction="Pick up the red cube and hold it at least 5 cm above the table.",
    objects=[_cube("red_cube", "red"), _cube("blue_cube", "blue")],
    difficulty=1,
))
_register(PlaceTask(
    id="place",
    title="Place in circle",
    instruction="Put the blue cube inside the green circle on the table and let go of it.",
    objects=[_cube("blue_cube", "blue"), _cube("red_cube", "red")],
    fixtures=[FixtureSpec("target", "zone", "green", 0.035)],
    difficulty=1,
))
_register(PushTask(
    id="push",
    title="Push puck",
    instruction="Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.",
    objects=[ObjSpec("puck", "puck", "orange", (0.03, 0.02), 0.05)],
    fixtures=[FixtureSpec("target", "zone", "green", 0.04)],
    theta_range=(-0.8, 0.8),
    difficulty=2,
))
_register(StackTask(
    id="stack",
    title="Stack",
    instruction="Stack the red cube on top of the blue cube and let go.",
    objects=[_cube("red_cube", "red"), _cube("blue_cube", "blue")],
    difficulty=2,
))
_register(TrayTask(
    id="tray",
    title="Into the tray",
    instruction="Put the yellow cube into the tray and let go of it.",
    objects=[_cube("yellow_cube", "yellow"), _cube("red_cube", "red")],
    fixtures=[FixtureSpec("tray", "tray", "purple")],
    theta_range=(-1.0, 1.0),
    difficulty=2,
))
_register(SortTask(
    id="sort",
    title="Sort by colour",
    instruction="Put the red cube into the red tray and the blue cube into the blue tray.",
    objects=[_cube("red_cube", "red"), _cube("blue_cube", "blue")],
    fixtures=[FixtureSpec("red_tray", "tray", "red"), FixtureSpec("blue_tray", "tray", "blue")],
    theta_range=(-1.15, 1.15),
    max_time=70.0,
    difficulty=3,
))

PILOT_TASKS = ("lift", "place", "push")


def get_task(task_id: str) -> Task:
    try:
        return TASKS[task_id]
    except KeyError:
        raise KeyError(f"unknown task '{task_id}'. Known: {', '.join(TASKS)}") from None
