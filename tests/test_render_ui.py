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
