"""Overhead-camera object poses for the real arm (EXPERIMENTAL).

Colour thresholding in HSV -> contour centroid and min-area-rect yaw -> table
coordinates through a homography fitted from 4+ pixel/table point pairs.
Needs opencv-python.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

HSV_RANGES = {  # (lo, hi) pairs; red wraps around hue 0
    "red": [((0, 120, 70), (8, 255, 255)), ((170, 120, 70), (180, 255, 255))],
    "blue": [((95, 120, 60), (130, 255, 255))],
    "green": [((40, 80, 60), (85, 255, 255))],
    "yellow": [((20, 120, 90), (35, 255, 255))],
    "orange": [((9, 140, 90), (19, 255, 255))],
}


def calibrate_homography(pixel_pts, table_pts, path="camera_calib.json") -> np.ndarray:
    """pixel_pts/table_pts: >= 4 matching points (u, v) and (x, y) in metres. Saves JSON."""
    import cv2

    H, _ = cv2.findHomography(np.asarray(pixel_pts, np.float32), np.asarray(table_pts, np.float32))
    Path(path).write_text(json.dumps({"H": H.tolist()}), encoding="utf-8")
    return H


class OverheadVision:
    def __init__(self, camera_index: int = 0, calib_path: str = "camera_calib.json", min_area_px: int = 120):
        import cv2

        self.cv2 = cv2
        self.cap = cv2.VideoCapture(camera_index)
        self.H = np.array(json.loads(Path(calib_path).read_text(encoding="utf-8"))["H"])
        self.min_area = min_area_px

    def _to_table(self, u, v):
        p = self.H @ np.array([u, v, 1.0])
        return p[0] / p[2], p[1] / p[2]

    def _blobs(self, frame, color):
        cv2 = self.cv2
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = None
        for lo, hi in HSV_RANGES[color]:
            m = cv2.inRange(hsv, np.array(lo), np.array(hi))
            mask = m if mask is None else (mask | m)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return sorted([c for c in contours if cv2.contourArea(c) >= self.min_area], key=cv2.contourArea, reverse=True)

    def detect(self, task) -> dict:
        ok, frame = self.cap.read()
        if not ok:
            return {"objects": {}, "fixtures": {}}
        out = {"objects": {}, "fixtures": {}}
        for o in task.objects:
            blobs = self._blobs(frame, o.color)
            if not blobs:
                continue
            (u, v), (w, h), ang = self.cv2.minAreaRect(blobs[0])
            x, y = self._to_table(u, v)
            yaw = math.radians(ang)
            yaw = (yaw + math.pi / 4) % (math.pi / 2) - math.pi / 4
            z = o.size[0] / 2 if o.shape == "cube" else o.size[1] / 2
            out["objects"][o.name] = {"pos": [round(x, 4), round(y, 4), z], "yaw": round(yaw, 4), "shape": o.shape, "color": o.color}
        for f in task.fixtures:
            blobs = self._blobs(frame, f.color)
            if blobs:
                (u, v), _, _ = self.cv2.minAreaRect(blobs[-1] if f.kind == "zone" else blobs[0])
                x, y = self._to_table(u, v)
                out["fixtures"][f.name] = {"pos": [round(x, 4), round(y, 4), 0.0], "kind": f.kind, "color": f.color}
        return out
