"""Start the Knack console, launch one real practice run from the UI, screenshot it every second (1920x1080)."""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "console")
OUT.mkdir(parents=True, exist_ok=True)
ui = subprocess.Popen([sys.executable, "-m", "knack", "ui", "--no-browser", "--port", "8765", "--runs", "runs"])
time.sleep(4)


def runs():
    try:
        return json.loads(urllib.request.urlopen("http://127.0.0.1:8765/api/runs", timeout=5).read())
    except Exception:
        return []


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    pg.goto("http://127.0.0.1:8765/")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(OUT / "onboarding.jpg"), type="jpeg", quality=92)
    if pg.locator("#obok").is_visible():
        pg.click("#obok")
    pg.select_option("#task", "lift")
    pg.select_option("#coder", "super")
    pg.select_option("#realism", "vision")
    pg.fill("#rounds", "6")
    pg.fill("#n", "8")
    pg.wait_for_timeout(500)
    pg.screenshot(path=str(OUT / "setup.jpg"), type="jpeg", quality=92)
    pg.click("#go")
    t0 = time.time()
    i = 0
    done_at = None
    while time.time() - t0 < 30 * 60:
        pg.screenshot(path=str(OUT / f"{i:05d}.jpg"), type="jpeg", quality=88)
        i += 1
        r = runs()
        if r and r[0].get("status") in ("done", "error"):
            done_at = done_at or time.time()
            if time.time() - done_at > 8:
                break
        time.sleep(1.0)
    rid = r[0]["run_id"] if r else None
    print("run", rid, "status", r[0].get("status") if r else None, "frames", i, flush=True)
    # final views: skill card and each round's analysis/diff
    pg.reload()
    pg.wait_for_timeout(2500)
    pg.screenshot(path=str(OUT / "final_top.jpg"), type="jpeg", quality=92)
    pg.screenshot(path=str(OUT / "final_full.jpg"), type="jpeg", quality=92, full_page=True)
    for tab in ("diff", "notes", "code"):
        try:
            pg.click(f'.tabs button[data-view="{tab}"]')
            pg.wait_for_timeout(800)
            pg.screenshot(path=str(OUT / f"final_{tab}.jpg"), type="jpeg", quality=92)
        except Exception as e:
            print("tab", tab, e)
    (OUT / "run.json").write_text(json.dumps(r[0] if r else {}, indent=1))
    b.close()
ui.terminate()
