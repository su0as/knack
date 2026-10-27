"""Run Knack's OpenCV 5 colour pipeline on ordinary RGB photos (no depth, no calibration).

This is a perception-only check: the same HSV ranges, morphology, connected components, size gating and minAreaRect
used by `knack.vision` in simulation, applied to photos. Without depth or a calibrated camera it reports image-space
detections (centre, size, angle), not table coordinates. Usage:

    python -m knack.photo_check <image dir> <out dir> [--truth truth.json]

truth.json maps file name -> {"red": n, "blue": n}; the script reports per-colour counts against it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .vision import HSV_RANGES

COLORS = ("red", "blue")
DRAW = {"red": (40, 40, 255), "blue": (255, 120, 30)}


def detect(bgr: np.ndarray, min_frac: float = 0.0015, max_frac: float = 0.08):
    import cv2

    h, w = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    k = max(3, int(round(min(h, w) / 200)) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    out, masks = {}, {}
    for c in COLORS:
        m = np.zeros((h, w), np.uint8)
        for lo, hi in HSV_RANGES[c]:
            m |= cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel)
        masks[c] = m
        n, labels, stats, cents = cv2.connectedComponentsWithStats(m, connectivity=8)
        dets = []
        for i in range(1, n):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < min_frac * h * w or area > max_frac * h * w:
                continue
            ys, xs = np.nonzero(labels == i)
            (cx, cy), (rw, rh), ang = cv2.minAreaRect(np.stack([xs, ys], 1).astype(np.float32))
            dets.append({"center": [round(float(cx), 1), round(float(cy), 1)], "size": [round(float(rw), 1), round(float(rh), 1)],
                         "angle": round(float(ang), 1), "pixels": int(area)})
        out[c] = dets
    return out, masks


def render(bgr, dets, masks, path):
    import cv2

    ann = bgr.copy()
    tint = np.zeros_like(bgr)
    for c in COLORS:
        tint[masks[c] > 0] = DRAW[c]
        for d in dets[c]:
            box = cv2.boxPoints(((d["center"][0], d["center"][1]), tuple(d["size"]), d["angle"])).astype(np.int32)
            cv2.drawContours(ann, [box], 0, (255, 255, 255), 3)
            cv2.drawContours(ann, [box], 0, DRAW[c], 2)
            cv2.drawMarker(ann, (int(d["center"][0]), int(d["center"][1])), (255, 255, 255), cv2.MARKER_CROSS, 18, 2)
            cv2.putText(ann, c, (int(d["center"][0]) + 10, int(d["center"][1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    strip = np.concatenate([bgr, tint, ann], axis=1)
    cv2.imwrite(str(path), strip)


def main(argv=None):
    import cv2

    ap = argparse.ArgumentParser()
    ap.add_argument("images")
    ap.add_argument("out")
    ap.add_argument("--truth")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    truth = json.loads(Path(a.truth).read_text()) if a.truth else {}
    rows = []
    for p in sorted(Path(a.images).glob("*")):
        if p.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        bgr = cv2.imread(str(p))
        dets, masks = detect(bgr)
        render(bgr, dets, masks, out / f"{p.stem}_pipeline.jpg")
        got = {c: len(dets[c]) for c in COLORS}
        t = truth.get(p.name, {})
        rows.append({"image": p.name, "detected": got, "truth": t, "detections": dets})
        print(p.name, "detected", got, "truth", t)
    (out / "photo_check.json").write_text(json.dumps({"opencv": cv2.__version__, "rows": rows}, indent=1))
    return rows


if __name__ == "__main__":
    main()
