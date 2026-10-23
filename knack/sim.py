"""MuJoCo scene builder and simulation environment.

The arm is built from primitives with SO-101-like proportions (see
kinematics.SIM_ARM). Everything is generated in Python, so there are no mesh
assets to download and it runs on CPU on Windows, macOS and Linux.
"""
from __future__ import annotations

import math
import os

import mujoco
import numpy as np

from .kinematics import HOME_TCP, JOINT_NAMES, SIM_ARM, ArmGeometry, ik
from .tasks import COLORS, TRAY_INNER, TRAY_WALL_H, FixtureSpec, ObjSpec, Task

TIMESTEP = 0.002
CTRL_DT = 0.02
GRIP_OPEN = SIM_ARM.finger_travel
GRIP_CLOSED = 0.0

_BODY_RGBA = "0.16 0.18 0.22 1"
_ACCENT_RGBA = "0.93 0.94 0.95 1"
_FINGER_RGBA = "0.10 0.11 0.13 1"


def _rgba(color: str, alpha: float | None = None) -> str:
    r, g, b, a = COLORS[color]
    return f"{r} {g} {b} {alpha if alpha is not None else a}"


def _quat_yaw(yaw: float) -> str:
    return f"{math.cos(yaw / 2)} 0 0 {math.sin(yaw / 2)}"


def arm_xml(g: ArmGeometry) -> str:
    palm_end = g.l3 - 0.02
    palm_start = 0.03
    palm_cx = (palm_start + palm_end) / 2
    palm_hx = (palm_end - palm_start) / 2
    lo = g.joint_limits
    return f"""
    <body name="arm_base" pos="{g.base[0]} {g.base[1]} 0">
      <geom name="base_shell" type="cylinder" size="0.05 0.025" pos="0 0 0.025" rgba="{_BODY_RGBA}" contype="0" conaffinity="0"/>
      <body name="pan_link" pos="0 0 0.05" gravcomp="1">
        <inertial pos="0 0 0.02" mass="0.15" diaginertia="2e-4 2e-4 2e-4"/>
        <joint name="shoulder_pan" axis="0 0 1" range="{lo[0][0]} {lo[0][1]}" damping="1.0" armature="0.01"/>
        <geom type="cylinder" size="0.032 0.025" pos="0 0 0.025" rgba="{_ACCENT_RGBA}" contype="0" conaffinity="0"/>
        <body name="upper_arm" pos="0 0 {g.shoulder_height - 0.05}" gravcomp="1">
          <inertial pos="{g.l1 / 2} 0 0" mass="0.12" diaginertia="2e-4 2e-4 2e-4"/>
          <joint name="shoulder_lift" axis="0 -1 0" range="{lo[1][0]} {lo[1][1]}" damping="1.0" armature="0.01"/>
          <geom type="capsule" fromto="0 0 0 {g.l1} 0 0" size="0.018" rgba="{_BODY_RGBA}" contype="0" conaffinity="0"/>
          <body name="forearm" pos="{g.l1} 0 0" gravcomp="1">
            <inertial pos="{g.l2 / 2} 0 0" mass="0.10" diaginertia="1.5e-4 1.5e-4 1.5e-4"/>
            <joint name="elbow_flex" axis="0 -1 0" range="{lo[2][0]} {lo[2][1]}" damping="0.8" armature="0.01"/>
            <geom type="capsule" fromto="0 0 0 {g.l2} 0 0" size="0.015" rgba="{_ACCENT_RGBA}" contype="0" conaffinity="0"/>
            <body name="wrist" pos="{g.l2} 0 0" gravcomp="1">
              <inertial pos="0.015 0 0" mass="0.05" diaginertia="3e-5 3e-5 3e-5"/>
              <joint name="wrist_flex" axis="0 -1 0" range="{lo[3][0]} {lo[3][1]}" damping="0.5" armature="0.005"/>
              <geom type="capsule" fromto="0 0 0 0.03 0 0" size="0.014" rgba="{_BODY_RGBA}" contype="0" conaffinity="0"/>
              <body name="hand" pos="0 0 0" gravcomp="1">
                <inertial pos="{palm_cx} 0 0" mass="0.08" diaginertia="5e-5 5e-5 5e-5"/>
                <joint name="wrist_roll" axis="1 0 0" range="{lo[4][0]} {lo[4][1]}" damping="0.3" armature="0.005"/>
                <geom name="palm" type="box" pos="{palm_cx} 0 0" size="{palm_hx} 0.034 0.013" rgba="{_BODY_RGBA}" friction="1.0 0.02 0.0001"/>
                <body name="finger_l" pos="{g.l3} 0.004 0" gravcomp="1">
                  <inertial pos="0 0 0" mass="0.01" diaginertia="2e-6 2e-6 2e-6"/>
                  <joint name="finger_l" type="slide" axis="0 1 0" range="0 {g.finger_travel + 0.001}" damping="25.0" armature="0.002"/>
                  <geom name="finger_l" type="box" pos="-0.00375 0 0" size="0.01625 0.004 0.01" rgba="{_FINGER_RGBA}" friction="1.5 0.02 0.0001" condim="4"/>
                </body>
                <body name="finger_r" pos="{g.l3} -0.004 0" gravcomp="1">
                  <inertial pos="0 0 0" mass="0.01" diaginertia="2e-6 2e-6 2e-6"/>
                  <joint name="finger_r" type="slide" axis="0 -1 0" range="0 {g.finger_travel + 0.001}" damping="25.0" armature="0.002"/>
                  <geom name="finger_r" type="box" pos="-0.00375 0 0" size="0.01625 0.004 0.01" rgba="{_FINGER_RGBA}" friction="1.5 0.02 0.0001" condim="4"/>
                </body>
                <site name="tcp" pos="{g.l3} 0 0" size="0.004" rgba="1 0.2 0.2 0.6" group="4"/>
              </body>
            </body>
          </body>
        </body>
      </body>
    </body>"""


def _object_xml(o: ObjSpec, pose: dict, mass_scale: float, fric_scale: float) -> str:
    x, y, yaw = pose["x"], pose["y"], pose["yaw"]
    if o.shape == "cube":
        h = o.size[0] / 2
        return f"""
    <body name="{o.name}" pos="{x} {y} {h + 0.0005}" quat="{_quat_yaw(yaw)}">
      <freejoint name="{o.name}"/>
      <geom name="{o.name}" type="box" size="{h} {h} {h}" rgba="{_rgba(o.color)}" mass="{o.mass * mass_scale}"
            friction="{1.2 * fric_scale} 0.02 0.0001" condim="4"/>
    </body>"""
    if o.shape == "puck":
        rad, height = o.size
        return f"""
    <body name="{o.name}" pos="{x} {y} {height / 2 + 0.0005}">
      <freejoint name="{o.name}"/>
      <geom name="{o.name}" type="cylinder" size="{rad} {height / 2}" rgba="{_rgba(o.color)}" mass="{o.mass * mass_scale}"
            friction="{0.3 * fric_scale} 0.005 0.0001" condim="3" priority="1"/>
    </body>"""
    raise ValueError(o.shape)


def _fixture_xml(f: FixtureSpec, pose: dict) -> str:
    x, y = pose["x"], pose["y"]
    if f.kind == "zone":
        return f"""
    <geom name="{f.name}" type="cylinder" size="{f.radius} 0.0006" pos="{x} {y} 0.0006" rgba="{_rgba(f.color, 0.55)}" contype="0" conaffinity="0"/>"""
    if f.kind == "tray":
        w = 0.003  # wall half-thickness
        o = TRAY_INNER + w
        h = TRAY_WALL_H / 2
        L = TRAY_INNER + 2 * w
        rgba = _rgba(f.color, 1.0)
        return f"""
    <body name="{f.name}" pos="{x} {y} 0">
      <geom name="{f.name}_floor" type="box" size="{L} {L} 0.002" pos="0 0 0.002" rgba="{rgba}" friction="0.8 0.01 0.0001"/>
      <geom name="{f.name}_wn" type="box" size="{L} {w} {h}" pos="0 {o} {h}" rgba="{rgba}"/>
      <geom name="{f.name}_ws" type="box" size="{L} {w} {h}" pos="0 {-o} {h}" rgba="{rgba}"/>
      <geom name="{f.name}_we" type="box" size="{w} {L} {h}" pos="{o} 0 {h}" rgba="{rgba}"/>
      <geom name="{f.name}_ww" type="box" size="{w} {L} {h}" pos="{-o} 0 {h}" rgba="{rgba}"/>
    </body>"""
    raise ValueError(f.kind)


def scene_xml(task: Task, layout: dict, dr: dict | None = None, g: ArmGeometry = SIM_ARM) -> str:
    dr = dr or {}
    objs = "".join(
        _object_xml(o, layout[o.name], dr.get(f"{o.name}_mass", 1.0), dr.get(f"{o.name}_friction", 1.0))
        for o in task.objects
    )
    fixtures = "".join(_fixture_xml(f, layout[f.name]) for f in task.fixtures)
    finger_force = dr.get("grip_force", 6.0)
    return f"""<mujoco model="knack-{task.id}">
  <compiler angle="radian" autolimits="true"/>
  <option timestep="{TIMESTEP}" integrator="implicitfast" cone="elliptic" impratio="10"/>
  <visual>
    <global offwidth="960" offheight="720"/>
    <quality shadowsize="2048"/>
    <headlight ambient="0.40 0.40 0.40" diffuse="0.32 0.32 0.32" specular="0.03 0.03 0.03"/>
  </visual>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.74 0.75 0.77" rgb2="0.66 0.67 0.70" width="512" height="512"/>
    <material name="grid" texture="grid" texrepeat="10 10" reflectance="0.04"/>
    <texture name="sky" type="skybox" builtin="gradient" rgb1="0.20 0.22 0.26" rgb2="0.06 0.07 0.09" width="256" height="256"/>
  </asset>
  <worldbody>
    <light name="key" pos="0.3 -0.4 1.2" dir="-0.2 0.3 -1" diffuse="0.6 0.6 0.6" castshadow="true"/>
    <geom name="table" type="box" size="0.5 0.45 0.02" pos="0.15 0 -0.02" material="grid" friction="0.5 0.01 0.0001"/>
    <body name="look_target" pos="0.16 0 0.03"/>
    <camera name="overhead" mode="targetbody" target="look_target" pos="0.36 0 0.48" fovy="50"/>
    <camera name="front" mode="targetbody" target="look_target" pos="0.47 -0.25 0.28" fovy="44"/>
    <camera name="side" mode="targetbody" target="look_target" pos="0.17 -0.46 0.10" fovy="44"/>
{arm_xml(g)}
{fixtures}
{objs}
  </worldbody>
  <contact>
    <exclude body1="finger_l" body2="finger_r"/>
  </contact>
  <actuator>
    <position name="a_shoulder_pan" joint="shoulder_pan" kp="40"/>
    <position name="a_shoulder_lift" joint="shoulder_lift" kp="40"/>
    <position name="a_elbow_flex" joint="elbow_flex" kp="30"/>
    <position name="a_wrist_flex" joint="wrist_flex" kp="15"/>
    <position name="a_wrist_roll" joint="wrist_roll" kp="8"/>
    <position name="a_finger_l" joint="finger_l" kp="400" ctrlrange="0 {g.finger_travel + 0.001}" forcelimited="true" forcerange="-{finger_force} {finger_force}"/>
    <position name="a_finger_r" joint="finger_r" kp="400" ctrlrange="0 {g.finger_travel + 0.001}" forcelimited="true" forcerange="-{finger_force} {finger_force}"/>
  </actuator>
</mujoco>"""


# "sim": light randomisation. "real": closer to a cheap arm with an overhead camera
# (wider mass/friction/grip ranges here; ~8 mm position and ~0.08 rad yaw noise in robot.py).
REALISM = {
    "sim": {"mass": (0.8, 1.25), "friction": (0.85, 1.15), "grip": (5.0, 7.0), "pos_noise": 0.002, "yaw_noise": 0.02},
    "real": {"mass": (0.6, 2.0), "friction": (0.5, 1.1), "grip": (3.5, 6.5), "pos_noise": 0.008, "yaw_noise": 0.08},
}


def sample_dr(task: Task, rng: np.random.Generator, realism: str = "sim") -> dict:
    """Domain randomisation (mass, friction, grip force). Ranges depend on the realism preset."""
    r = REALISM[realism]
    dr = {}
    for o in task.objects:
        dr[f"{o.name}_mass"] = float(rng.uniform(*r["mass"]))
        dr[f"{o.name}_friction"] = float(rng.uniform(*r["friction"]))
    dr["grip_force"] = float(rng.uniform(*r["grip"]))
    return dr


class SimEnv:
    """One randomised scene. Deterministic given (task, seed)."""

    def __init__(self, task: Task, seed: int, *, randomize: bool = True, render_size=(320, 240), geometry: ArmGeometry = SIM_ARM,
                 realism: str = "sim"):
        self.task = task
        self.realism = realism
        self.seed = int(seed)
        self.geometry = geometry
        self.rng = np.random.default_rng(self.seed)
        self.layout = task.sample_layout(self.rng)
        self.dr = sample_dr(task, self.rng, realism) if randomize else {}
        self.xml = scene_xml(task, self.layout, self.dr, geometry)
        self.model = mujoco.MjModel.from_xml_string(self.xml)
        self.data = mujoco.MjData(self.model)
        m = self.model
        self.n_sub = int(round(CTRL_DT / m.opt.timestep))
        jid = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n) for n in JOINT_NAMES]
        self.arm_qadr = np.array([m.jnt_qposadr[j] for j in jid])
        self.arm_dadr = np.array([m.jnt_dofadr[j] for j in jid])
        self.arm_act = np.array([mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, f"a_{n}") for n in JOINT_NAMES])
        self.finger_qadr = np.array([m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in ("finger_l", "finger_r")])
        self.finger_act = np.array([mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in ("a_finger_l", "a_finger_r")])
        self.tcp_site = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, "tcp")
        self.finger_geoms = {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, n) for n in ("finger_l", "finger_r")}
        self.fl_geom = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "finger_l")
        self.fr_geom = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "finger_r")
        self.gripper_geoms = self.finger_geoms | {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "palm")}
        self.table_geom = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "table")
        self.obj_body = {o.name: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, o.name) for o in task.objects}
        self.obj_geom = {o.name: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, o.name) for o in task.objects}
        self.obj_spec = {o.name: o for o in task.objects}
        self.fixture_spec = {f.name: f for f in task.fixtures}
        self._renderer = None
        self._renderer_size = None
        self._render_failed = False
        self.render_error = None
        self.render_size = tuple(render_size)
        self._tick_callbacks = []
        self.grip_target = GRIP_OPEN
        self.reset_arm()

    # ---------- state ----------
    @property
    def time(self) -> float:
        return float(self.data.time)

    def reset_arm(self, tcp=HOME_TCP):
        q = ik(tcp, None, self.geometry)
        self.data.qpos[self.arm_qadr] = q
        self.data.ctrl[self.arm_act] = q
        self.data.qpos[self.finger_qadr] = GRIP_OPEN
        self.data.ctrl[self.finger_act] = GRIP_OPEN
        mujoco.mj_forward(self.model, self.data)
        self.step_seconds(0.3)
        self.data.time = 0.0

    def arm_q(self) -> np.ndarray:
        return self.data.qpos[self.arm_qadr].copy()

    def arm_qvel(self) -> np.ndarray:
        return self.data.qvel[self.arm_dadr].copy()

    def tcp(self) -> np.ndarray:
        return self.data.site_xpos[self.tcp_site].copy()

    def finger_opening(self) -> float:
        return float(self.data.qpos[self.finger_qadr].sum())

    def set_arm_target(self, q):
        self.data.ctrl[self.arm_act] = np.asarray(q, dtype=float)

    def arm_target(self) -> np.ndarray:
        return self.data.ctrl[self.arm_act].copy()

    def set_grip(self, travel: float):
        self.grip_target = float(np.clip(travel, 0.0, self.geometry.finger_travel))
        self.data.ctrl[self.finger_act] = self.grip_target

    # ---------- stepping ----------
    def add_tick_callback(self, fn):
        self._tick_callbacks.append(fn)

    def _physics(self, n: int):
        m, d = self.model, self.data
        for _ in range(n):
            mujoco.mj_step(m, d)

    def tick(self):
        """Advance one control period (CTRL_DT) and run callbacks."""
        self._physics(self.n_sub)
        for cb in self._tick_callbacks:
            cb(self)

    def step_seconds(self, seconds: float):
        self._physics(max(1, int(round(seconds / self.model.opt.timestep))))

    # ---------- objects ----------
    def object_pose(self, name: str):
        b = self.obj_body[name]
        pos = self.data.xpos[b].copy()
        w, x, y, z = self.data.xquat[b]
        yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        return pos, float(yaw)

    def object_tilt(self, name: str) -> float:
        b = self.obj_body[name]
        zaxis = self.data.xmat[b].reshape(3, 3)[:, 2]
        return float(math.acos(max(-1.0, min(1.0, zaxis[2]))))

    def fixture_pos(self, name: str) -> np.ndarray:
        p = self.layout[name]
        return np.array([p["x"], p["y"], 0.0])

    def _contacts_with(self, geom: int) -> set:
        out = set()
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            if c.geom1 == geom:
                out.add(c.geom2)
            elif c.geom2 == geom:
                out.add(c.geom1)
        return out

    def is_held(self, name: str) -> bool:
        g = self.obj_geom[name]
        touching = self._contacts_with(g)
        return self.fl_geom in touching and self.fr_geom in touching and self.finger_opening() > 0.004

    def held_object(self):
        for name in self.obj_geom:
            if self.is_held(name):
                return name
        return None

    def gripper_table_force(self) -> float:
        """Largest normal force between the gripper and the table (N)."""
        f6 = np.zeros(6)
        worst = 0.0
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            pair = {c.geom1, c.geom2}
            if self.table_geom in pair and pair & self.gripper_geoms:
                mujoco.mj_contactForce(self.model, self.data, i, f6)
                worst = max(worst, abs(float(f6[0])))
        return worst

    # ---------- rendering ----------
    def render(self, camera: str = "front", size=None):
        if self._render_failed:
            return None
        w, h = size or self.render_size
        try:
            if self._renderer is None or self._renderer_size != (w, h):
                if self._renderer is not None:
                    self._renderer.close()
                self._renderer = mujoco.Renderer(self.model, height=h, width=w)
                self._renderer_size = (w, h)
            self._renderer.update_scene(self.data, camera=camera)
            return self._renderer.render().copy()
        except Exception as e:  # no OpenGL available (headless without EGL/OSMesa)
            self._render_failed = True
            self.render_error = f"{type(e).__name__}: {e}"
            if os.environ.get("KNACK_DEBUG"):
                raise
            return None

    def close(self):
        if self._renderer is not None:
            try:
                self._renderer.close()
            except Exception:
                pass
            self._renderer = None
