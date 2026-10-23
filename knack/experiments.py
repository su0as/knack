"""Experiments behind the measured findings.

pilot      day-1 go/no-go gate (Super vs Ultra on the 3 pilot tasks)
scoreboard success and $/skill per coder model (Nano, Super, Ultra, DeepSeek baseline)
ablation   reward source: ground truth vs vision judge vs self-report
judge      vision-judge accuracy and abstention vs ground truth on stored episodes
plots      charts from the JSON outputs (needs matplotlib)

Every function writes JSON next to its runs so numbers in the README trace back to files.
"""
from __future__ import annotations

import glob
import json
import random
import time
from pathlib import Path

from .agent import LearnConfig, Learner
from .config import resolve_model
from .tasks import PILOT_TASKS

# Approximate readings of ASPIRE's published success-vs-API-cost chart (LIBERO-Pro).
# Different benchmark from Knack's scenes: plotted as context only, never as a head-to-head.
ASPIRE_REFERENCE = [
    {"label": "Kimi K3 (ASPIRE, LIBERO-Pro)", "success": 0.78, "usd_per_task": 55.0},
    {"label": "Qwen 3.8 Max (ASPIRE, LIBERO-Pro)", "success": 0.56, "usd_per_task": 40.0},
    {"label": "Haiku 5.5 (ASPIRE, LIBERO-Pro)", "success": 0.68, "usd_per_task": 4.0},
]


def _stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def _row(card: dict, model: str, task: str, reward: str) -> dict:
    ev = card.get("eval") or {}
    return {
        "model": model, "model_id": resolve_model(model).id, "task": task, "reward": reward,
        "run_id": card["run_id"], "status": card.get("status"),
        "round_success": [r["success"] for r in card["rounds"]],
        "rounds_used": len(card["rounds"]),
        "eval_k": ev.get("k"), "eval_n": ev.get("n"), "eval_p": ev.get("p"), "eval_lo": ev.get("lo"), "eval_hi": ev.get("hi"),
        "usd": card["receipt"]["total_usd"], "llm_usd": card["receipt"]["llm_usd"],
        "tokens_in": card["receipt"]["prompt_tokens"], "tokens_out": card["receipt"]["completion_tokens"],
        "wall_s": card.get("wall_time_s"), "self_report_true": ev.get("self_report_true"), "judge": ev.get("judge"),
        "mock": card.get("mock", False),
    }


def _sweep(name: str, combos: list, budget_usd: float, runs_root: str, common: dict) -> tuple[Path, list]:
    out = Path(runs_root) / f"{name}-{_stamp()}"
    out.mkdir(parents=True, exist_ok=True)
    rows, spent = [], 0.0
    for model, task, reward in combos:
        remaining = budget_usd - spent
        if remaining <= 0.001:
            rows.append({"model": model, "task": task, "reward": reward, "status": "skipped (budget)"})
            continue
        cfg = LearnConfig(task=task, coder=model, reward=reward, budget_usd=remaining, runs_root=str(out),
                          save_to_library=False, **common)
        try:
            card = Learner(cfg).run()
            row = _row(card, model, task, reward)
            spent += row["usd"]
        except Exception as e:  # keep the sweep going; record the failure honestly
            row = {"model": model, "task": task, "reward": reward, "status": f"failed: {type(e).__name__}: {str(e)[:200]}"}
        rows.append(row)
        (out / f"{name}.json").write_text(json.dumps({"rows": rows, "spent_usd": round(spent, 4), "budget_usd": budget_usd,
                                                      "common": common}, indent=1), encoding="utf-8")
        print(json.dumps({k: row.get(k) for k in ("model", "task", "reward", "eval_p", "usd", "status")}))
    return out, rows


def pilot(models=("super", "ultra"), tasks=PILOT_TASKS, rounds=4, episodes=8, eval_episodes=50, budget_usd=0.9,
          runs_root="runs", workers=None, mock=False, realism="sim") -> dict:
    common = dict(rounds=rounds, episodes=episodes, eval_episodes=eval_episodes, workers=workers, mock=mock, realism=realism)
    out, rows = _sweep("pilot", [(m, t, "gt") for m in models for t in tasks], budget_usd, runs_root, common)
    verdict = {}
    for m in models:
        mine = [r for r in rows if r["model"] == m and r.get("eval_p") is not None]
        passed = [r["task"] for r in mine if r["eval_p"] >= 0.5]
        verdict[m] = {"tasks_at_50pct": passed, "pass": len(passed) >= 2}
    gate = any(v["pass"] for v in verdict.values())
    summary = {"gate_pass": gate, "criterion": "held-out success >= 50% on at least 2 of 3 tasks within 4 rounds",
               "by_model": verdict, "rows": rows}
    (out / "pilot.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    lines = ["# Pilot gate", "", f"**Gate: {'PASS' if gate else 'FAIL'}** ({summary['criterion']})", "",
             "| model | task | rounds | per-round success | held-out | USD |", "|---|---|---|---|---|---|"]
    for r in rows:
        if r.get("eval_p") is None:
            lines.append(f"| {r['model']} | {r['task']} | | | {r.get('status')} | |")
            continue
        rs = " ".join(f"{x:.0%}" for x in r["round_success"])
        lines.append(f"| {r['model']} | {r['task']} | {r['rounds_used']} | {rs} | {r['eval_k']}/{r['eval_n']} ({r['eval_p']:.0%}, CI {r['eval_lo']:.0%}-{r['eval_hi']:.0%}) | ${r['usd']:.3f} |")
    (out / "pilot.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return summary


def scoreboard(models=("nano", "super", "ultra", "deepseek-flash"), tasks=("lift", "place", "push", "stack", "tray"),
               rounds=4, episodes=8, eval_episodes=100, budget_usd=5.0, runs_root="runs", workers=None, mock=False,
               realism="sim") -> dict:
    common = dict(rounds=rounds, episodes=episodes, eval_episodes=eval_episodes, workers=workers, mock=mock, realism=realism)
    out, rows = _sweep("scoreboard", [(m, t, "gt") for m in models for t in tasks], budget_usd, runs_root, common)
    table = {}
    for m in models:
        mine = [r for r in rows if r["model"] == m and r.get("eval_p") is not None]
        if mine:
            table[m] = {"model_id": resolve_model(m).id, "tasks": len(mine),
                        "mean_success": sum(r["eval_p"] for r in mine) / len(mine),
                        "usd_per_skill": sum(r["usd"] for r in mine) / len(mine),
                        "solved_50": sum(r["eval_p"] >= 0.5 for r in mine)}
    res = {"table": table, "rows": rows, "aspire_reference": ASPIRE_REFERENCE}
    (out / "scoreboard_summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


def ablation(tasks=("lift", "place", "stack"), coder="super", rewards=("gt", "vlm", "self"), rounds=4, episodes=8,
             eval_episodes=100, budget_usd=3.0, runs_root="runs", workers=None, mock=False, realism="sim") -> dict:
    common = dict(rounds=rounds, episodes=episodes, eval_episodes=eval_episodes, workers=workers, mock=mock, realism=realism)
    out, rows = _sweep("ablation", [(coder, t, rw) for rw in rewards for t in tasks], budget_usd, runs_root, common)
    table = {}
    for rw in rewards:
        mine = [r for r in rows if r["reward"] == rw and r.get("eval_p") is not None]
        if mine:
            table[rw] = {"mean_heldout_success": sum(r["eval_p"] for r in mine) / len(mine),
                         "mean_usd": sum(r["usd"] for r in mine) / len(mine),
                         "self_report_true_rate": sum((r.get("self_report_true") or 0) for r in mine) / max(1, sum(r["eval_n"] for r in mine))}
    res = {"table": table, "rows": rows}
    (out / "ablation_summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


def collect_episodes(patterns: list[str]) -> list[dict]:
    """Episodes with ground truth and end frames from stored runs."""
    eps = []
    for pat in patterns:
        for f in glob.glob(str(Path(pat) / "**" / "result.json"), recursive=True):
            try:
                r = json.loads(Path(f).read_text(encoding="utf-8"))
            except Exception:
                continue
            if (r.get("frames") or {}).get("end_front") and r.get("success_gt") is not None:
                r["_dir"] = str(Path(f).parent)
                eps.append(r)
    return eps


def judge_eval(patterns: list[str], n: int = 100, model: str = "super-vl", thresholds=(0.0, 0.5, 0.6, 0.7, 0.8, 0.9),
               out_root="runs", seed: int = 0, budget_usd: float = 0.5) -> dict:
    """Balanced sample of stored episodes -> judge -> accuracy / abstention vs ground truth."""
    from .judge import VLMJudge, parse_verdict
    from .llm import Ledger, LLMClient
    from .stats import judge_metrics
    from .tasks import get_task

    eps = collect_episodes(patterns)
    pos = [e for e in eps if e["success_gt"]]
    neg = [e for e in eps if not e["success_gt"]]
    rng = random.Random(seed)
    rng.shuffle(pos)
    rng.shuffle(neg)
    half = n // 2
    sample = pos[:half] + neg[: n - min(half, len(pos))]
    out = Path(out_root) / f"judge-eval-{_stamp()}"
    out.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(out / "ledger.jsonl", budget_usd=budget_usd)
    judge = VLMJudge(LLMClient(ledger), model=model, threshold=0.0)
    rows = []
    for e in sample:
        v = judge.judge(get_task(e["task"]).instruction, e["frames"], e["_dir"])
        rows.append({"dir": e["_dir"], "task": e["task"], "gt": bool(e["success_gt"]), "pred": v.success, "conf": v.confidence,
                     "reason": v.reason, "error": v.error})
    curve = []
    for th in thresholds:
        pairs = [(r["gt"], (r["pred"] if (r["pred"] is not None and r["conf"] >= th) else None)) for r in rows]
        curve.append({"threshold": th, **judge_metrics(pairs)})
    res = {"model": resolve_model(model).id, "n": len(rows), "positives": sum(r["gt"] for r in rows), "curve": curve,
           "usd": round(ledger.total_usd(), 5), "rows": rows}
    (out / "judge_eval.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


def plots(paths: list[str], out_dir: str = "docs/figures") -> list[str]:
    """Render charts from scoreboard / ablation / judge-eval / run JSON. Needs matplotlib."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    ink, lime, red, grey = "#0b0e12", "#9fd400", "#ff5d3d", "#8a94a3"
    for p in paths:
        p = Path(p)
        data = json.loads(p.read_text(encoding="utf-8"))
        if "table" in data and "aspire_reference" in data:  # scoreboard
            fig, ax = plt.subplots(figsize=(7, 4.5))
            for m, row in data["table"].items():
                ax.scatter(row["usd_per_skill"], row["mean_success"], s=90, color=lime if resolve_model(m).nvidia else red, zorder=3)
                ax.annotate(m, (row["usd_per_skill"], row["mean_success"]), xytext=(6, 4), textcoords="offset points")
            for ref in data["aspire_reference"]:
                ax.scatter(ref["usd_per_task"], ref["success"], s=60, facecolors="none", edgecolors=grey, zorder=2)
                ax.annotate(ref["label"], (ref["usd_per_task"], ref["success"]), xytext=(6, -10), textcoords="offset points", fontsize=7, color=grey)
            ax.set_xscale("log")
            ax.set_xlabel("USD per skill / per task (log)")
            ax.set_ylabel("held-out success")
            ax.set_ylim(0, 1.02)
            ax.set_title("Knack scoreboard (filled) vs ASPIRE-reported points (hollow, different benchmark)", fontsize=9)
            f = out / "scoreboard.png"
            fig.tight_layout()
            fig.savefig(f, dpi=160)
            plt.close(fig)
            written.append(str(f))
        elif "curve" in data:  # judge eval
            fig, ax = plt.subplots(figsize=(6, 4))
            cov = [1 - (c["abstain_rate"] or 0) for c in data["curve"]]
            acc = [c["accuracy"] or 0 for c in data["curve"]]
            ax.plot(cov, acc, marker="o", color=lime)
            for c, x, y in zip(data["curve"], cov, acc):
                ax.annotate(f"t={c['threshold']}", (x, y), xytext=(4, 4), textcoords="offset points", fontsize=7)
            ax.set_xlabel("coverage (1 - abstention)")
            ax.set_ylabel("accuracy on decided episodes")
            ax.set_title(f"Vision judge vs ground truth ({data['model']}, n={data['n']})", fontsize=9)
            f = out / "judge_coverage.png"
            fig.tight_layout()
            fig.savefig(f, dpi=160)
            plt.close(fig)
            written.append(str(f))
        elif "rows" in data:  # pilot / ablation / scoreboard rows -> success vs round curves
            fig, ax = plt.subplots(figsize=(7, 4))
            for r in data["rows"]:
                if r.get("round_success"):
                    ax.plot(range(1, len(r["round_success"]) + 1), r["round_success"], marker="o", alpha=0.8,
                            label=f"{r['model']}/{r['task']}/{r['reward']}")
            ax.set_xlabel("practice round")
            ax.set_ylabel("round success")
            ax.set_ylim(0, 1.02)
            ax.legend(fontsize=6, ncol=2)
            f = out / f"{p.stem}_curves.png"
            fig.tight_layout()
            fig.savefig(f, dpi=160)
            plt.close(fig)
            written.append(str(f))
    return written
