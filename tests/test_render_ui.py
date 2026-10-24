import json
import threading
import urllib.request

import pytest

from knack.sim import SimEnv
from knack.tasks import get_task


def test_render_cameras():
    env = SimEnv(get_task("stack"), 0)
    img = env.render("front")
    if img is None:
        pytest.skip(f"no OpenGL here: {env.render_error}")
    assert img.shape == (240, 320, 3) and img.mean() > 10
    for cam in ("side", "overhead"):
        assert env.render(cam) is not None
    env.close()


def test_console_ids_exist():
    """Every $("id") used by app.js must exist in index.html."""
    import re
    from pathlib import Path

    static = Path(__file__).resolve().parent.parent / "knack" / "ui" / "static"
    js = (static / "app.js").read_text(encoding="utf-8")
    html = (static / "index.html").read_text(encoding="utf-8")
    ids = set(re.findall(r'\$\("([a-zA-Z0-9_-]+)"\)', js))
    assert ids, "no ids found"
    missing = sorted(i for i in ids if f'id="{i}"' not in html)
    assert not missing, missing


def test_ui_server_endpoints(tmp_path):
    from http.server import ThreadingHTTPServer

    from knack.ui.server import Handler

    run = tmp_path / "r1"
    run.mkdir()
    (run / "state.json").write_text(json.dumps({"task": "lift", "status": "done", "updated": 1, "models": {}}))
    (run / "best_skill.py").write_text("def run(robot):\n    pass\n")
    Handler.runs_root = tmp_path
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{port}"
        tasks = json.loads(urllib.request.urlopen(base + "/api/tasks").read())
        assert {t["id"] for t in tasks} >= {"lift", "push", "sort"}
        runs = json.loads(urllib.request.urlopen(base + "/api/runs").read())
        assert runs[0]["run_id"] == "r1"
        assert b"def run" in urllib.request.urlopen(base + "/api/runs/r1/file/best_skill.py").read()
        html = urllib.request.urlopen(base + "/").read()
        assert b"KNACK" in html
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(base + "/api/runs/r1/file/../../etc/passwd")
    finally:
        srv.shutdown()


def test_list_runs_marks_dead_runs_stale(tmp_path):
    import json
    import os
    import time

    from knack.ui.server import list_runs

    d = tmp_path / "20261024-000000-push-super-gt-real"
    d.mkdir()
    f = d / "state.json"
    f.write_text(json.dumps({"task": "push", "status": "running", "updated": 1}), encoding="utf-8")
    old = time.time() - 3600
    os.utime(f, (old, old))
    assert list_runs(tmp_path)[0]["status"].startswith("stale")
    f.write_text(json.dumps({"task": "push", "status": "running", "updated": 1}), encoding="utf-8")
    assert list_runs(tmp_path)[0]["status"] == "running"
