"""Skill library: verified skills are saved and offered to the coder for later tasks."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .config import library_dir

_STOP = {"the", "a", "an", "and", "of", "to", "it", "on", "in", "into", "so", "that", "its", "is", "at", "let", "go", "put"}


def _words(s: str) -> set:
    return {w for w in re.findall(r"[a-z]+", s.lower()) if w not in _STOP}


class SkillLibrary:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else library_dir()
        self.index_path = self.root / "index.json"

    def entries(self) -> list:
        if not self.index_path.exists():
            return []
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def add(self, task_id: str, instruction: str, code: str, card: dict, run_dir: str | Path | None = None) -> Path:
        run_id = card.get("run_id", "run")
        d = self.root / task_id / run_id
        d.mkdir(parents=True, exist_ok=True)
        (d / "skill.py").write_text(code, encoding="utf-8")
        (d / "card.json").write_text(json.dumps(card, indent=1), encoding="utf-8")
        if run_dir and (Path(run_dir) / "card.html").exists():
            shutil.copy(Path(run_dir) / "card.html", d / "card.html")
        ev = card.get("eval", {})
        entry = {
            "task": task_id, "instruction": instruction, "run_id": run_id, "path": str(d.as_posix()),
            "success": ev.get("p"), "ci": [ev.get("lo"), ev.get("hi")], "n": ev.get("n"),
            "coder": card.get("models", {}).get("coder"), "usd": card.get("receipt", {}).get("total_usd"),
        }
        entries = [e for e in self.entries() if not (e["task"] == task_id and e["run_id"] == run_id)]
        entries.append(entry)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(entries, indent=1), encoding="utf-8")
        return d

    def best_for(self, task_id: str):
        cands = [e for e in self.entries() if e["task"] == task_id and e.get("success") is not None]
        return max(cands, key=lambda e: (e["success"], -(e.get("usd") or 0)), default=None)

    def retrieve(self, instruction: str, k: int = 2, exclude_task: str | None = None, min_success: float = 0.5) -> list:
        """Top-k verified skills by word overlap with the instruction (best run per task)."""
        q = _words(instruction)
        best: dict[str, dict] = {}
        for e in self.entries():
            if exclude_task and e["task"] == exclude_task:
                continue
            if (e.get("success") or 0) < min_success:
                continue
            if e["task"] not in best or (e["success"] or 0) > (best[e["task"]]["success"] or 0):
                best[e["task"]] = e
        scored = []
        for e in best.values():
            w = _words(e["instruction"])
            score = len(q & w) / max(1, len(q | w))
            scored.append((score, e))
        scored.sort(key=lambda t: -t[0])
        out = []
        for score, e in scored[:k]:
            p = Path(e["path"]) / "skill.py"
            if p.exists():
                out.append({**e, "code": p.read_text(encoding="utf-8"), "score": round(score, 3),
                            "success_text": f"{e['success']:.0%}" if e.get("success") is not None else "?"})
        return out
