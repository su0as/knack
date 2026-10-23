"""Parallel episode runners.

LocalRunner: one OS process per chunk of episodes (spawn start method, works on
Windows/macOS/Linux), with a wall-clock kill for hung skills.
The Nebius Serverless Jobs runner lives in knack/nebius.py and reuses this one
inside the container.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import time
from pathlib import Path

from .worker import child_main, failed_result, write_result


def default_workers() -> int:
    n = os.cpu_count() or 2
    return max(1, min(16, n - 1 if n > 2 else n))


class LocalRunner:
    name = "local"

    def __init__(self, workers: int | None = None, wall_factor: float = 1.5, wall_slack: float = 45.0, chunk_size: int = 1):
        self.workers = workers or default_workers()
        self.wall_factor = wall_factor
        self.wall_slack = wall_slack
        self.chunk_size = max(1, chunk_size)
        self.compute_seconds = 0.0  # summed wall time of worker processes

    def _deadline(self, chunk: list) -> float:
        from .tasks import get_task

        total = 0.0
        for s in chunk:
            mt = float(s.get("max_time") or get_task(s["task"]).max_time)
            total += mt * self.wall_factor + self.wall_slack
        return total

    def run_batch(self, specs: list, out_root, on_update=None) -> list:
        """Run all specs; return results in the same order. on_update(event, seed, result|None)."""
        out_root = Path(out_root)
        out_root.mkdir(parents=True, exist_ok=True)
        ctx = mp.get_context("spawn")
        chunks = [specs[i:i + self.chunk_size] for i in range(0, len(specs), self.chunk_size)]
        pending = list(chunks)
        running: list[dict] = []
        results: dict[int, dict] = {}

        def out_dir(spec):
            return out_root / f"ep_{spec['seed']}"

        def collect(chunk, timed_out: bool):
            for spec in chunk:
                seed = int(spec["seed"])
                if seed in results:
                    continue
                f = out_dir(spec) / "result.json"
                if f.exists():
                    try:
                        results[seed] = json.loads(f.read_text(encoding="utf-8"))
                    except Exception as e:
                        results[seed] = failed_result(spec, "HarnessError", f"unreadable result.json: {e}")
                else:
                    kind = "WallTimeout" if timed_out else "WorkerCrash"
                    msg = "skill exceeded the wall-clock limit (infinite loop?)" if timed_out else "worker process died"
                    results[seed] = failed_result(spec, kind, msg)
                    write_result(out_dir(spec), results[seed])
                if on_update:
                    on_update("done", seed, results[seed])

        while pending or running:
            while pending and len(running) < self.workers:
                chunk = pending.pop(0)
                dirs = [str(out_dir(s)) for s in chunk]
                for d in dirs:
                    Path(d).mkdir(parents=True, exist_ok=True)
                    stale = Path(d) / "result.json"
                    if stale.exists():
                        stale.unlink()
                p = ctx.Process(target=child_main, args=(chunk, dirs), daemon=True)
                p.start()
                running.append({"p": p, "chunk": chunk, "t0": time.time(), "deadline": time.time() + self._deadline(chunk)})
                if on_update:
                    for s in chunk:
                        on_update("running", int(s["seed"]), None)
            still = []
            for job in running:
                p = job["p"]
                if not p.is_alive():
                    p.join()
                    self.compute_seconds += time.time() - job["t0"]
                    collect(job["chunk"], timed_out=False)
                elif time.time() > job["deadline"]:
                    p.terminate()
                    p.join(5)
                    self.compute_seconds += time.time() - job["t0"]
                    collect(job["chunk"], timed_out=True)
                else:
                    still.append(job)
            running = still
            time.sleep(0.05)
        return [results[int(s["seed"])] for s in specs]


def run_inline(specs: list, out_root) -> list:
    """Run episodes in this process (no isolation). Handy for tests and debugging."""
    from .worker import run_episode

    out_root = Path(out_root)
    return [run_episode(s, out_root / f"ep_{s['seed']}") for s in specs]
