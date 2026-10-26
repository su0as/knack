"""OpenCV 5 perception from simulated RGB-D cameras (`--realism vision`).

Instead of reading object poses from the simulator, the robot looks at the scene:

  render RGB + depth (overhead camera, front camera as backup)
  -> OpenCV 5: HSV colour masks, morphology, connected components
  -> back-project mask pixels to 3D with the camera intrinsics and pose
  -> top-face selection, cv2.minAreaRect in the table plane for centre and yaw

Static fixtures (target circles, trays) are mapped once at the start of the episode, like a
real cell would be. Objects are detected on every observe(). Anything the cameras cannot see
(typically a cube under the gripper) is simply missing from the observation, and get_pose()
raises PerceptionError, so the skill has to move out of the way and look again.

Every detection is compared with the simulator's true pose and the error is logged, so the
perception quality is measured, not assumed (see `summary()`).
"""
from __future__ import annotations

import math

import numpy as np

# OpenCV hue is 0-180. Ranges cover the scene palette in knack.tasks.COLORS under the scene lighting.
HSV_RANGES = {
    "red": [((0, 90, 40), (8, 255, 255)), ((168, 90, 40), (180, 255, 255))],
    "orange": [((9, 110, 60), (19, 255, 255))],
    "yellow": [((20, 110, 60), (35, 255, 255))],
    "green": [((45, 45, 40), (88, 255, 255))],
    "blue": [((98, 90, 40), (124, 255, 255))],
    "purple": [((125, 70, 40), (160, 255, 255))],
}
CAMERAS = ("overhead", "front")
MIN_PIXELS = 40
TRAY_OUTER = 0.050  # outer half-size of a tray (tasks.TRAY_INNER + 2 x wall)
TRAY_WALL_TOP = 0.025


class PerceptionError(LookupError):
    """The object is not visible from the cameras right now. Skills may catch it (LookupError)."""


def wrap_quarter(yaw: float) -> float:
    return (yaw + math.pi / 4) % (math.pi / 2) - math.pi / 4


# A perfect synthetic render would make perception look better than any real camera. These model a consumer
# RGB-D camera on a hobby cell: per-pixel depth noise growing with distance, 1 mm depth quantisation, RGB noise,
# and a per-episode extrinsic calibration error the pipeline does not know about.
SENSOR = {"depth_sigma_at_1m": 0.004, "depth_quant": 0.001, "rgb_sigma": 4.0,
          "calib_trans_m": 0.003, "calib_rot_deg": 0.4}


def _rot(axis, deg):
    axis = np.asarray(axis, float) / (np.linalg.norm(axis) or 1.0)
    a = math.radians(deg)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K


class VisionPerception:
    def __init__(self, env, size=(640, 480), sensor: dict | None = SENSOR):
        import cv2
        import mujoco

        self.cv2 = cv2
        self.mujoco = mujoco
        self.env = env
        self.w, self.h = size
        self._renderer = None
        self._kernel = np.ones((3, 3), np.uint8)
        self.cam_id = {c: mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_CAMERA, c) for c in CAMERAS}
        self.fixtures: dict | None = None
        self.calls = 0
        self.lookups = 0
        self.misses = 0
        self.errors_mm: list[float] = []
        self.yaw_errors_deg: list[float] = []
        self.by_camera = {c: 0 for c in CAMERAS}
        self.last_error: str | None = None
        self.observe_ms: list[float] = []
        self.sensor = sensor
        self._rng = np.random.default_rng(int(env.seed) + 31_337)
        self._calib = {}
        for c in CAMERAS:  # fixed for the episode: the camera was mounted/calibrated slightly wrong
            if sensor:
                self._calib[c] = (_rot(self._rng.normal(size=3), self._rng.normal(0, sensor["calib_rot_deg"])),
                                  self._rng.normal(0, sensor["calib_trans_m"] / math.sqrt(3), size=3))
            else:
                self._calib[c] = (np.eye(3), np.zeros(3))

    # ------------------------------------------------------------------ capture
    def _r(self):
        if self._renderer is None:
            self._renderer = self.mujoco.Renderer(self.env.model, height=self.h, width=self.w)
        return self._renderer

    def capture(self, cam: str):
        r = self._r()
        r.update_scene(self.env.data, camera=cam)
        rgb = r.render().copy()
        r.enable_depth_rendering()
        r.update_scene(self.env.data, camera=cam)
        depth = r.render().copy()
        r.disable_depth_rendering()
        if self.sensor:
            sn = self.sensor
            depth = depth + self._rng.normal(0.0, 1.0, depth.shape).astype(depth.dtype) * (sn["depth_sigma_at_1m"] * depth ** 2)
            depth = np.round(depth / sn["depth_quant"]) * sn["depth_quant"]
            rgb = np.clip(rgb.astype(np.float32) + self._rng.normal(0.0, sn["rgb_sigma"], rgb.shape), 0, 255).astype(np.uint8)
        return rgb, depth

    def to_world(self, cam: str, depth: np.ndarray, us: np.ndarray, vs: np.ndarray) -> np.ndarray:
        """Pixel coordinates + depth -> world points, pinhole model from the MuJoCo camera."""
        cid = self.cam_id[cam]
        fovy = float(self.env.model.cam_fovy[cid])
        f = 0.5 * self.h / math.tan(math.radians(fovy) / 2)
        z = depth[vs, us].astype(np.float64)
        x = (us + 0.5 - self.w / 2) / f * z
        y = -(vs + 0.5 - self.h / 2) / f * z
        pc = np.stack([x, y, -z], axis=1)
        R = self.env.data.cam_xmat[cid].reshape(3, 3)
        dR, dt = self._calib[cam]
        return pc @ (dR @ R).T + self.env.data.cam_xpos[cid] + dt

    def color_mask(self, rgb: np.ndarray, color: str) -> np.ndarray:
        cv2 = self.cv2
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        mask = np.zeros(hsv.shape[:2], np.uint8)
        for lo, hi in HSV_RANGES[color]:
            mask |= cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
        return cv2.morphologyEx(mask, cv2.MORPH_OPEN, self._kernel)

    def _largest_component(self, mask: np.ndarray):
        n, labels, stats, _ = self.cv2.connectedComponentsWithStats(mask, connectivity=8)
        if n <= 1:
            return None
        k = 1 + int(np.argmax(stats[1:, self.cv2.CC_STAT_AREA]))
        if stats[k, self.cv2.CC_STAT_AREA] < MIN_PIXELS:
            return None
        vs, us = np.nonzero(labels == k)
        return us, vs

    def _rect(self, xy: np.ndarray):
        """minAreaRect in the table plane (mm, float32). Returns centre (m) and angle (rad)."""
        (cx, cy), _, ang = self.cv2.minAreaRect((xy * 1000.0).astype(np.float32))
        return np.array([cx, cy]) / 1000.0, math.radians(ang)

    # ------------------------------------------------------------------ fixtures (mapped once)
    def map_fixtures(self) -> dict:
        env = self.env
        rgb, depth = self.capture("overhead")
        out = {}
        for name, f in env.fixture_spec.items():
            mask = self.color_mask(rgb, f.color)
            comp = self._largest_component(mask)
            if comp is None:
                continue
            us, vs = comp
            pts = self.to_world("overhead", depth, us, vs)
            if f.kind == "zone":
                pts = pts[pts[:, 2] < 0.006]
                if len(pts) < MIN_PIXELS:
                    continue
                c = np.median(pts[:, :2], axis=0)
            else:
                pts = pts[pts[:, 2] < TRAY_WALL_TOP + 0.004]
                if len(pts) < MIN_PIXELS:
                    continue
                c, _ = self._rect(pts[:, :2])
            out[name] = np.array([c[0], c[1], 0.0])
        self.fixtures = out
        return out

    # ------------------------------------------------------------------ objects
    def _detect(self, name, cam, rgb, depth):
        env = self.env
        spec = env.obj_spec[name]
        mask = self.color_mask(rgb, spec.color)
        vs, us = np.nonzero(mask)
        if len(us) < MIN_PIXELS:
            return None
        pts = self.to_world(cam, depth, us, vs)
        keep = pts[:, 2] > 0.004  # nothing at floor level (zones, shadows)
        for fname, fspec in env.fixture_spec.items():  # drop same-coloured tray walls and floor
            if fspec.kind == "tray" and fspec.color == spec.color and self.fixtures and fname in self.fixtures:
                fc = self.fixtures[fname]
                # generous margin: the tray pose itself is estimated (a few mm off); a cube's top face sits above the rim
                inside = (np.abs(pts[:, 0] - fc[0]) < TRAY_OUTER + 0.015) & (np.abs(pts[:, 1] - fc[1]) < TRAY_OUTER + 0.015)
                keep &= ~(inside & (pts[:, 2] < TRAY_WALL_TOP + 0.003))
        if keep.sum() < MIN_PIXELS:
            return None
        clean = np.zeros_like(mask)
        clean[vs[keep], us[keep]] = 255
        # candidate blobs, largest first; reject anything bigger than the object could be (leftover tray walls etc.)
        n, labels, stats, _ = self.cv2.connectedComponentsWithStats(clean, connectivity=8)
        order = sorted(range(1, n), key=lambda k: -stats[k, self.cv2.CC_STAT_AREA])
        max_extent = (spec.size[0] * 1.6) if spec.shape == "cube" else (spec.size[0] * 2.6)
        for k in order:
            if stats[k, self.cv2.CC_STAT_AREA] < MIN_PIXELS:
                return None
            vs_k, us_k = np.nonzero(labels == k)
            pts = self.to_world(cam, depth, us_k, vs_k)
            top_z = float(np.percentile(pts[:, 2], 95))
            top = pts[pts[:, 2] >= top_z - 0.004]
            if len(top) < 15:
                top = pts
            _, (w, h), _ = self.cv2.minAreaRect((top[:, :2] * 1000.0).astype(np.float32))
            if max(w, h) / 1000.0 <= max_extent:
                us = us_k
                break
        else:
            return None
        c, ang = self._rect(top[:, :2])
        half = spec.size[0] / 2 if spec.shape == "cube" else spec.size[1] / 2
        yaw = wrap_quarter(ang) if spec.shape == "cube" else 0.0
        return {"pos": [float(c[0]), float(c[1]), top_z - half], "yaw": yaw, "pixels": int(len(us)), "camera": cam}

    def observe(self) -> dict:
        """{"objects": {name: entry}, "fixtures": {name: xyz}}. Missing objects are not visible."""
        import time as _t

        t0 = _t.perf_counter()
        try:
            return self._observe()
        finally:
            self.observe_ms.append((_t.perf_counter() - t0) * 1000.0)

    def _observe(self) -> dict:
        self.calls += 1
        if self.fixtures is None:
            self.map_fixtures()
        frames = {}
        objects = {}
        for name in self.env.obj_spec:
            self.lookups += 1
            det = None
            for cam in CAMERAS:
                if cam not in frames:
                    frames[cam] = self.capture(cam)
                det = self._detect(name, cam, *frames[cam])
                if det:
                    break
            if det is None:
                self.misses += 1
                continue
            self.by_camera[det["camera"]] += 1
            true_pos, true_yaw = self.env.object_pose(name)
            self.errors_mm.append(float(np.linalg.norm(np.array(det["pos"]) - true_pos) * 1000.0))
            if self.env.obj_spec[name].shape == "cube":
                self.yaw_errors_deg.append(abs(math.degrees(wrap_quarter(det["yaw"] - true_yaw))))
            objects[name] = det
        return {"objects": objects, "fixtures": self.fixtures or {}}

    def summary(self) -> dict:
        e = np.array(self.errors_mm) if self.errors_mm else np.array([np.nan])
        y = np.array(self.yaw_errors_deg) if self.yaw_errors_deg else np.array([0.0])
        return {
            "calls": self.calls, "lookups": self.lookups, "misses": self.misses,
            "detection_rate": round(1 - self.misses / self.lookups, 4) if self.lookups else None,
            "pos_err_mm_median": round(float(np.nanmedian(e)), 2), "pos_err_mm_p90": round(float(np.nanpercentile(e, 90)), 2),
            "yaw_err_deg_median": round(float(np.nanmedian(y)), 2),
            "by_camera": dict(self.by_camera),
            "ms_per_observe_median": round(float(np.median(self.observe_ms)), 1) if self.observe_ms else None,
            "fixtures_mapped": sorted((self.fixtures or {}).keys()),
            "fixture_err_mm": {n: round(float(np.linalg.norm(p - self.env.fixture_pos(n)) * 1000.0), 2)
                               for n, p in (self.fixtures or {}).items()},
        }

    def close(self):
        if self._renderer is not None:
            try:
                self._renderer.close()
            except Exception:
                pass
            self._renderer = None


def annotate(env, out_dir, cam: str = "overhead", size=(640, 480)) -> dict:
    """Write the perception pipeline's intermediate images for one scene: RGB, depth, colour masks, and the
    detections drawn on the image (contour, rotated box, label with estimated vs true position)."""
    import cv2
    from pathlib import Path

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    v = VisionPerception(env, size=size)
    seen = v.observe()
    rgb, depth = v.capture(cam)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(out / f"{cam}_rgb.png"), bgr)
    d = depth.copy()
    near, far = np.percentile(d, 1), np.percentile(d, 99)
    dn = np.clip((d - near) / max(1e-6, far - near), 0, 1)
    cv2.imwrite(str(out / f"{cam}_depth.png"), cv2.applyColorMap((255 * (1 - dn)).astype(np.uint8), cv2.COLORMAP_VIRIDIS))
    masks = np.zeros_like(bgr)
    ann = bgr.copy()
    colors = sorted({o.color for o in env.obj_spec.values()} | {f.color for f in env.fixture_spec.values()})
    for c in colors:
        m = v.color_mask(rgb, c)
        tint = {"red": (60, 60, 230), "blue": (230, 120, 40), "green": (80, 200, 80), "yellow": (40, 210, 240),
                "orange": (40, 140, 250), "purple": (200, 80, 150)}.get(c, (255, 255, 255))
        masks[m > 0] = tint
        cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(ann, [k for k in cnts if cv2.contourArea(k) >= MIN_PIXELS], -1, tint, 2)
    cv2.imwrite(str(out / f"{cam}_masks.png"), masks)
    f = 0.5 * v.h / math.tan(math.radians(float(env.model.cam_fovy[v.cam_id[cam]])) / 2)
    R = env.data.cam_xmat[v.cam_id[cam]].reshape(3, 3)
    t = env.data.cam_xpos[v.cam_id[cam]]

    def project(p):
        pc = R.T @ (np.asarray(p) - t)
        return int(round(v.w / 2 + f * pc[0] / -pc[2] - 0.5)), int(round(v.h / 2 - f * pc[1] / -pc[2] - 0.5))

    rows = []
    for name, det in seen["objects"].items():
        true, _ = env.object_pose(name)
        err = float(np.linalg.norm(np.array(det["pos"]) - true) * 1000)
        u, w = project(det["pos"])
        cv2.drawMarker(ann, (u, w), (255, 255, 255), cv2.MARKER_CROSS, 14, 2)
        cv2.putText(ann, f"{name} {err:.1f}mm", (u + 8, w - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        rows.append({"name": name, "est": [round(x, 4) for x in det["pos"]], "true": [round(float(x), 4) for x in true],
                     "err_mm": round(err, 2), "pixels": det["pixels"], "camera": det["camera"]})
    for name, pos in seen["fixtures"].items():
        u, w = project(pos)
        cv2.circle(ann, (u, w), 5, (255, 255, 255), 2)
        cv2.putText(ann, name, (u + 8, w + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imwrite(str(out / f"{cam}_detections.png"), ann)
    strip = np.concatenate([bgr, cv2.imread(str(out / f"{cam}_depth.png")), masks, ann], axis=1)
    cv2.imwrite(str(out / f"{cam}_pipeline.png"), strip)
    v.close()
    return {"objects": rows, "summary": v.summary()}
