"""Copy the small summary files of local runs into a results folder (same filter as the live workflow),
so runs made on a laptop (for example console takes for the video) can be committed to the `results` branch.

    git worktree add ../knack-results results
    python scripts/publish_results.py runs/<run_id> [runs/<run_id> ...] --dest ../knack-results/results/<stamp>-<label>
    cd ../knack-results && git add -A && git commit -m "results: <label>" && git push origin results

Per-episode frames and traces stay local (they are large); everything a number in the README comes from is copied.
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

KEEP = {"card.json", "card.md", "card.html", "config.json", "ledger.jsonl", "events.jsonl", "round.json", "summary.md",
        "notes.md", "diff.patch", "skill.py", "best_skill.py", "eval.json", "selection.json", "state.json"}
KEY = re.compile(r"v1\.[A-Za-z0-9_-]{40,}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--dest", required=True)
    a = ap.parse_args()
    dest = Path(a.dest)
    n = 0
    for r in a.runs:
        src = Path(r)
        if not (src / "config.json").exists():
            print(f"skip {src}: not a run directory")
            continue
        for p in src.rglob("*"):
            if not p.is_file() or "episodes" in p.relative_to(src).parts:
                continue
            if p.name in KEEP or (p.suffix in (".json", ".md") and p.stat().st_size < 2_000_000):
                text = p.read_text(encoding="utf-8", errors="ignore")
                if KEY.search(text):
                    raise SystemExit(f"refusing to copy {p}: it looks like it contains an API key")
                out = dest / src.name / p.relative_to(src)
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, out)
                n += 1
        log = src.parent / f"{src.name}.log"  # console runs write their stdout next to the run directory
        if log.exists():
            shutil.copy2(log, dest / src.name / "console.log")
            n += 1
    print(f"copied {n} files into {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
