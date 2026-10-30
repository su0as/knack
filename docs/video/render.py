"""Render the Knack demo video: HTML composition -> frames (Playwright) + synthesized music/SFX + narration -> MP4.

Inputs (docs/video/build/): replay/ (from footage.py), console_art/console/ (from capture_console.py).
Run `python render.py prep` to only write build/assets.js (for previewing composition.html in a browser).
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
FPS = 30
SR = 48000

REGIONS = {  # console layout at 1920x1080 (x, y, w, h)
    "chips": [330, 8, 1200, 44],
    "code": [1505, 548, 410, 528],
    "grid": [12, 252, 1474, 436],
    "round": [12, 218, 540, 34],
    "analysis": [1505, 300, 410, 236],
    "curve": [1505, 138, 410, 152],
}


def prep():
    tl = json.loads((HERE / "timeline.json").read_text())
    rep = json.loads((BUILD / "replay/report.json").read_text())
    replay = {"r1": {}, "r2": {}}
    z = {"r1": {}, "r2": {}}
    for k, v in rep.items():
        name, sub = k.split("/")
        if name in ("r1", "r2"):
            replay[name][sub] = v["frames"]
            z[name][sub] = v["metrics"]["red_cube_z"]
        else:
            replay[f"{name}_{sub}"] = v["frames"]
    hero_cam = "side" if replay.get("hero_r1_side", 0) > 0 else "front"
    hero_cm = round((rep["hero_r1/" + hero_cam]["metrics"]["red_cube_z"] - 0.015) * 100, 2) if replay.get("hero_r1_" + hero_cam) else 4.93
    if not replay.get("hero_r1_" + hero_cam):  # fall back to a tile clip
        hero_cam = "front"
    summary = (HERE / "hero/round_1_summary.md").read_text()
    diff = [ln for ln in (HERE / "hero/round_2_diff.patch").read_text().splitlines() if ln[:1] in "+-" and not ln.startswith(("+++", "---"))][:40]
    assets = {"replay": replay, "z": z, "heroCam": hero_cam, "heroCm": hero_cm, "summary": summary, "diff": diff, "regions": REGIONS}
    (BUILD / "assets.js").write_text("window.TL=" + json.dumps(tl) + ";\nwindow.ASSETS=" + json.dumps(assets) + ";\nwindow.BASE='build/';\n")
    return tl, assets


def W(tl, k, word, n=1):
    c = 0
    for w in tl["words"][k]:
        if w["w"].lower().strip(".,:") == word:
            c += 1
            if c == n:
                return tl["starts"][k] + w["t"]
    return tl["starts"][k]


def decode(path):
    import numpy as np

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def audio(tl, out):
    import numpy as np

    T = tl["total"]
    n = int(T * SR) + SR
    t = np.arange(n) / SR
    voice = np.zeros(n, np.float32)
    for k, s in tl["starts"].items():
        v = decode(HERE / "audio" / f"{k}.mp3")
        i = int(s * SR)
        voice[i:i + len(v)] += v[: n - i]
    rng = np.random.default_rng(7)

    def env(a, d, length):
        e = np.ones(length)
        na, nd = int(a * SR), int(d * SR)
        e[:na] = np.linspace(0, 1, na) if na else 1
        if nd:
            e[-nd:] *= np.linspace(1, 0, nd)
        return e

    def lowpass(x, fc):
        X = np.fft.rfft(x)
        f = np.fft.rfftfreq(len(x), 1 / SR)
        X *= 1 / np.sqrt(1 + (f / fc) ** 4)
        return np.fft.irfft(X, len(x)).astype(np.float32)

    def note(f, dur, amp, harm=6, a=0.4, r=1.0):
        m = int(dur * SR)
        tt = np.arange(m) / SR
        y = sum((1 / h) * np.sin(2 * np.pi * f * h * tt * (1 + 0.0015 * (h % 2))) for h in range(1, harm + 1))
        return (amp * y * env(a, min(r, dur * 0.9), m)).astype(np.float32)

    def add(buf, start, sig):
        i = int(start * SR)
        if i >= len(buf) or i < 0:
            return
        buf[i:i + len(sig)] += sig[: len(buf) - i]

    music = np.zeros(n, np.float32)
    bpm = 100
    beat = 60 / bpm
    bar = 4 * beat
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)  # noqa: E731
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55, 60], [55, 59, 62]]  # Am F C G
    pad = np.zeros(n, np.float32)
    k = 0
    s0 = 0.0
    while s0 < T:
        ch = chords[k % 4]
        for m in ch:
            add(pad, s0, note(hz(m), 2 * bar + 0.6, 0.05, harm=5, a=0.9, r=1.2))
        add(pad, s0, note(hz(ch[0] - 24), 2 * bar + 0.4, 0.07, harm=3, a=0.5, r=1.0))
        s0 += 2 * bar
        k += 1
    pad = lowpass(pad, 1400)
    # intro: darker until the 8/8 moment, then open up
    E = tl["E"]
    open_ = np.clip((t - (E["flip"] - 0.15)) / 0.4, 0, 1)
    music += pad * (0.55 + 0.45 * open_)
    # pulse (kick + hat + pluck arp) in the console and closing sections
    S = tl["scenes"]
    sections = [(S["console"][0], S["console"][1]), (S["close"][0], T - 3.0)]
    kick_len = int(0.35 * SR)
    kt = np.arange(kick_len) / SR
    kick = (np.sin(2 * np.pi * (48 + 70 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 9) * 0.32).astype(np.float32)
    hat = (rng.standard_normal(int(0.05 * SR)) * np.exp(-np.arange(int(0.05 * SR)) / SR * 90) * 0.035).astype(np.float32)
    hat = hat - lowpass(hat, 6000)
    for a, b in sections:
        x = a
        i = 0
        while x < b:
            add(music, x, kick)
            add(music, x + beat / 2, hat)
            ch = chords[int(x // (2 * bar)) % 4]
            for j, m in enumerate(ch[:3] + [ch[1] + 12]):
                add(music, x + j * beat / 4, note(hz(m + 12), 0.22, 0.022, harm=3, a=0.005, r=0.2))
            x += beat
            i += 1
    # sound design
    sfx = np.zeros(n, np.float32)

    def blip(f, dur=0.12, amp=0.12):
        m = int(dur * SR)
        tt = np.arange(m) / SR
        return (amp * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 28)).astype(np.float32)

    def chime(amp=0.16):
        m = int(2.2 * SR)
        tt = np.arange(m) / SR
        y = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, a, d in [(880, 1, 2.2), (1320, .6, 2.8), (1760, .35, 3.5), (2637, .2, 4.5)])
        return (amp * y).astype(np.float32)

    def boom(amp=0.35):
        m = int(1.6 * SR)
        tt = np.arange(m) / SR
        return (amp * np.sin(2 * np.pi * (40 + 30 * np.exp(-tt * 6)) * tt) * np.exp(-tt * 2.5)).astype(np.float32)

    def whoosh(dur=0.6, amp=0.08):
        m = int(dur * SR)
        x = rng.standard_normal(m)
        x = lowpass(x, 2500) - lowpass(x, 300)
        e = np.sin(np.linspace(0, np.pi, m)) ** 2
        return (amp * x * e).astype(np.float32)

    def click(amp=0.05):
        m = int(0.025 * SR)
        x = rng.standard_normal(m) * np.exp(-np.arange(m) / SR * 300)
        return (amp * x).astype(np.float32)

    sent = "Pick up the red cube and hold it at least 5 cm above the table."
    for j in range(0, len(sent), 2):
        p = j / len(sent)
        tt = 0.4 + (1 - (1 - p) ** (1 / 3)) * 2.3
        add(sfx, tt, click(0.035))
    for i in range(8):
        add(sfx, E["r1badge"] + i * 0.11, blip(196, 0.16, 0.10))
    add(sfx, E["r1badge"] + 0.4, boom(0.22))
    add(sfx, W(tl, "v02", "less") - 0.05, blip(147, 0.3, 0.12))
    riser_s, riser_e = E["flip"] - 1.9, E["flip"] - 0.05
    m = int((riser_e - riser_s) * SR)
    rz = rng.standard_normal(m)
    rz = (lowpass(rz, 4000) - lowpass(rz, 400)) * np.linspace(0, 1, m) ** 2 * 0.07
    add(sfx, riser_s, rz.astype(np.float32))
    for i in range(8):
        add(sfx, E["r2badge"] + i * 0.05, blip(880 + i * 60, 0.1, 0.07))
    add(sfx, E["flip"], chime(0.17))
    add(sfx, E["flip"], boom(0.25))
    for i in range(0, 50, 3):
        add(sfx, E["sq"][0] + (i / 50) * (E["sq"][1] - E["sq"][0]), blip(1200 + i * 12, 0.05, 0.03))
    add(sfx, E["big"], chime(0.15))
    add(sfx, E["cost"], blip(660, 0.15, 0.06))
    add(sfx, E["title"][0] + 0.15, boom(0.38))
    add(sfx, E["title"][0] + 0.2, chime(0.10))
    for x in (E["rw"][0] - 0.05, E["held"][0] - 0.1, S["problem"][0] - 0.1, S["console"][0] - 0.2, S["findings"][0] - 0.2, S["close"][0] - 0.2):
        add(sfx, x, whoosh())
    nb = W(tl, "v06", "neither")
    add(sfx, nb, blip(220, 0.18, 0.08))
    add(sfx, nb + 0.2, blip(196, 0.18, 0.08))
    for key in (("v09", "six"), ("v09", "eighty-two"), ("v09", "approved"), ("v09", "millimetre"), ("v09", "zero")):
        add(sfx, W(tl, *key), blip(520, 0.12, 0.05))
    kn = W(tl, "v10", "knack")
    add(sfx, kn - 0.25, boom(0.35))
    add(sfx, kn - 0.2, chime(0.12))
    # ducking: music sits under the voice
    venv = np.abs(voice)
    w = int(0.25 * SR)
    venv = np.convolve(venv, np.ones(w) / w, mode="same")
    duck = np.clip(venv / 0.03, 0, 1)
    duck = np.convolve(duck, np.ones(int(0.3 * SR)) / int(0.3 * SR), mode="same")
    mus = music * (0.9 - 0.55 * duck)
    fade = np.clip((T - t) / 3.0, 0, 1) * np.clip(t / 1.5, 0, 1)
    mix = voice * 1.0 + mus * 0.9 * fade + sfx * 0.9
    mix = mix[: int(T * SR)]
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.89
    import wave

    with wave.open(str(out), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((mix * 32767).astype(np.int16).tobytes())


def frames(tl, video_only):
    from playwright.sync_api import sync_playwright

    N = int(tl["total"] * FPS)
    stills = BUILD / "stills"
    stills.mkdir(exist_ok=True)
    E = tl["E"]
    keep = {int(x * FPS) for x in (1.5, 6.0, E["r1badge"] + 1, E["close"][0] + 2, E["flip"] + 0.4, E["cost"] + 1, 45.0, 70.0, 95.0, 105.0, 112.0, 128.0, 138.0, 150.0, 160.0)}
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", str(video_only)], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        pg.goto((HERE / "composition.html").as_uri())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(800)
        for i in range(N):
            pg.evaluate(f"seek({i / FPS:.4f})")
            img = pg.screenshot(type="jpeg", quality=93)
            ff.stdin.write(img)
            if i in keep:
                (stills / f"t{i / FPS:06.1f}.jpg").write_bytes(img)
            if i % 300 == 0:
                print("frame", i, "/", N, flush=True)
        b.close()
    ff.stdin.close()
    ff.wait()


def main():
    tl, _ = prep()
    if len(sys.argv) > 1 and sys.argv[1] == "prep":
        return
    wav = BUILD / "audio.wav"
    audio(tl, wav)
    vid = BUILD / "video_only.mp4"
    frames(tl, vid)
    out = BUILD / "knack_nebius.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(vid), "-i", str(wav), "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    print("done", out, out.stat().st_size)


if __name__ == "__main__":
    main()
