"""Camera frames for the judge, the live console grid and replay GIFs."""
from __future__ import annotations

import io
import os
from pathlib import Path

import numpy as np

try:
    from PIL import Image
except ImportError:  # pillow is a hard dependency, but keep import errors readable
    Image = None

KEY_CAMERAS = ("front", "side", "overhead")


def encode_jpeg(arr: np.ndarray, quality: int = 85) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def atomic_write(path: Path, data: bytes):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


class Recorder:
    def __init__(self, env, out_dir, *, live_every: float = 0.5, gif_every: float | None = None,
                 live_camera: str = "front", size=(320, 240), gif_size=(240, 180)):
        self.env = env
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.live_every = live_every
        self.gif_every = gif_every
        self.live_camera = live_camera
        self.size = tuple(size)
        self.gif_size = tuple(gif_size)
        self._next_live = 0.0
        self._next_gif = 0.0
        self.gif_frames: list[np.ndarray] = []
        self.enabled = Image is not None
        env.add_tick_callback(self.on_tick)

    def on_tick(self, env):
        if not self.enabled:
            return
        t = env.time
        if self.live_every and t >= self._next_live:
            self._next_live = t + self.live_every
            img = env.render(self.live_camera, self.size)
            if img is None:
                self.enabled = False
                return
            atomic_write(self.out / "live.jpg", encode_jpeg(img, 70))
        if self.gif_every and t >= self._next_gif:
            self._next_gif = t + self.gif_every
            img = env.render(self.live_camera, self.gif_size)
            if img is not None:
                self.gif_frames.append(img)

    def keyframe(self, label: str, cameras=KEY_CAMERAS) -> dict:
        """Render and save `label_camera.jpg` for each camera. Returns {label_camera: filename}."""
        out = {}
        if not self.enabled:
            return out
        for cam in cameras:
            img = self.env.render(cam, self.size)
            if img is None:
                self.enabled = False
                break
            name = f"{label}_{cam}.jpg"
            atomic_write(self.out / name, encode_jpeg(img))
            out[f"{label}_{cam}"] = name
            if cam == self.live_camera:
                atomic_write(self.out / "live.jpg", encode_jpeg(img, 70))
        return out

    def save_gif(self, path=None, fps: int = 10) -> str | None:
        if not self.gif_frames:
            return None
        path = Path(path or (self.out / "episode.gif"))
        frames = [Image.fromarray(f) for f in self.gif_frames]
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0)
        return path.name
