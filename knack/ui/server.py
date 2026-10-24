"""Knack console: a small stdlib HTTP server over the runs/ directory.

    knack ui            -> http://127.0.0.1:8765

GET  /api/tasks, /api/models, /api/runs, /api/library
GET  /api/runs/<id>/state | /card | /file/<relative path>
POST /api/learn {task, instruction?, coder, reward, rounds, n, eval, budget, mock}
"""
from __future__ import annotations

import json
import mimetypes
import os
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

STATIC = Path(__file__).resolve().parent / "static"
STALE_S = 600  # a live run rewrites state.json every few seconds; 10 quiet minutes means it died


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_runs(root: Path) -> list:
    out = []
    if not root.exists():
        return out
    for state_file in root.glob("**/state.json"):
        if len(state_file.relative_to(root).parts) > 3:
            continue
        s = _read_json(state_file)
        if not s:
            continue
        ev = s.get("eval") or {}
        status = s.get("status")
        # A run that crashed hard (killed process, power loss) never writes a final status. If its state file
        # has not changed for STALE_S seconds while it claims to be running, show it as stale, not running.
        if status in ("running", "starting"):
            try:
                idle = time.time() - state_file.stat().st_mtime
            except OSError:
                idle = 0
            if idle > STALE_S:
                status = f"stale (no update for {int(idle // 60)} min)"
        out.append({
            "run_id": str(state_file.parent.relative_to(root).as_posix()), "task": s.get("task"), "status": status,
            "phase": s.get("phase"), "reward": s.get("reward"), "coder": (s.get("models") or {}).get("coder", {}).get("alias"),
            "eval_p": ev.get("p"), "updated": s.get("updated", 0), "mock": s.get("mock"), "instruction": s.get("instruction"),
            "total_usd": (s.get("cost") or {}).get("total_usd"),
        })
    out.sort(key=lambda r: -(r["updated"] or 0))
    return out


class Handler(BaseHTTPRequestHandler):
    runs_root: Path = Path("runs")
    server_version = "knack/0.1"

    def log_message(self, fmt, *args):  # quiet
        if os.environ.get("KNACK_DEBUG"):
            super().log_message(fmt, *args)

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj, default=str).encode(), "application/json")

    def _file(self, p: Path, root: Path):
        try:
            p = p.resolve()
            if not str(p).startswith(str(root.resolve())) or not p.is_file():
                return self._json({"error": "not found"}, 404)
            ctype = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
            if p.suffix in (".py", ".patch", ".md", ".txt", ".jsonl"):
                ctype = "text/plain; charset=utf-8"
            self._send(200, p.read_bytes(), ctype)
        except OSError:
            self._json({"error": "unreadable"}, 500)

    def do_GET(self):
        from ..config import MODELS
        from ..library import SkillLibrary
        from ..tasks import TASKS

        path = unquote(urlparse(self.path).path)
        root = self.runs_root
        if path in ("/", "/index.html"):
            return self._file(STATIC / "index.html", STATIC)
        if path.startswith("/static/"):
            return self._file(STATIC / path[len("/static/"):], STATIC)
        if path == "/api/tasks":
            return self._json([t.to_dict() for t in TASKS.values()])
        if path == "/api/models":
            return self._json({k: m.to_dict() for k, m in MODELS.items()})
        if path == "/api/runs":
            return self._json(list_runs(root))
        if path == "/api/library":
            return self._json(SkillLibrary().entries())
        if path.startswith("/api/runs/"):
            rest = path[len("/api/runs/"):]
            for key in ("/state", "/card", "/file/"):
                if key in rest:
                    run_id, sub = rest.split(key, 1)
                    d = (root / run_id)
                    if key == "/state":
                        return self._json(_read_json(d / "state.json") or {"error": "no state"})
                    if key == "/card":
                        return self._json(_read_json(d / "card.json") or {"error": "no card yet"})
                    return self._file(d / sub, d)
        return self._json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/learn":
            return self._json({"error": "not found"}, 404)
        n = int(self.headers.get("Content-Length", "0") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "bad json"}, 400)
        from ..tasks import TASKS

        task = body.get("task")
        if task not in TASKS:
            return self._json({"error": f"unknown task {task}"}, 400)
        coder = str(body.get("coder", "ultra"))
        reward = str(body.get("reward", "gt"))
        instruction = (body.get("instruction") or "").strip()
        if instruction and instruction != TASKS[task].instruction:
            reward = "vlm"
        else:
            instruction = ""
        realism = str(body.get("realism", "sim"))
        realism = realism if realism in ("sim", "real", "vision") else "sim"
        run_id = time.strftime("%Y%m%d-%H%M%S") + f"-{task}-{coder}-{reward}" + {"real": "-real", "vision": "-vision"}.get(realism, "")
        cmd = [sys.executable, "-m", "knack", "learn", task, "--run-id", run_id, "--coder", coder, "--reward", reward,
               "--rounds", str(int(body.get("rounds", 4))), "--n", str(int(body.get("n", 8))),
               "--eval", str(int(body.get("eval", 50))), "--budget", str(float(body.get("budget", 1.0))),
               "--runs", str(self.runs_root), "--realism", realism]
        if instruction:
            cmd += ["--instruction", instruction]
        if body.get("mock"):
            cmd.append("--mock")
        log = (self.runs_root / f"{run_id}.log")
        self.runs_root.mkdir(parents=True, exist_ok=True)
        with log.open("w", encoding="utf-8") as fh:
            kwargs = {"stdout": fh, "stderr": subprocess.STDOUT, "cwd": os.getcwd()}
            if os.name == "nt":
                kwargs["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["start_new_session"] = True
            subprocess.Popen(cmd, **kwargs)
        return self._json({"run_id": run_id, "cmd": " ".join(cmd)})


def serve(port: int = 8765, runs_root: str = "runs", open_browser: bool = True):
    Handler.runs_root = Path(runs_root)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Knack console on {url}  (runs: {Path(runs_root).resolve()})  Ctrl+C to stop")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
