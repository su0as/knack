"""knack command line."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from .config import MODELS, api_key, base_url, load_dotenv


def _print_json(obj):
    print(json.dumps(obj, indent=1, default=str))


def cmd_tasks(a):
    from .tasks import PILOT_TASKS, TASKS

    for t in TASKS.values():
        flag = " (pilot)" if t.id in PILOT_TASKS else ""
        print(f"{t.id:7s} difficulty {t.difficulty}  {t.instruction}{flag}")


def cmd_models(a):
    print(f"{'alias':15s} {'model id':42s} {'$in/M':>7s} {'$out/M':>7s}  vision  role")
    for m in MODELS.values():
        print(f"{m.alias:15s} {m.id:42s} {m.price_in:7.2f} {m.price_out:7.2f}  {'yes' if m.vision else '   '}     {m.note}")
    if a.remote:
        if not api_key():
            print("\nNEBIUS_API_KEY not set; skipping the remote check.")
            return 1
        from openai import OpenAI

        client = OpenAI(base_url=base_url(), api_key=api_key())
        ids = sorted(m.id for m in client.models.list().data)  # listing models is free
        print(f"\n{len(ids)} models visible at {base_url()}:")
        known = {m.id for m in MODELS.values()}
        for i in ids:
            print(("  * " if i in known else "    ") + i)
        missing = known - set(ids)
        if missing:
            print("\nIn Knack's catalogue but not listed by the API (check IDs / regions):", ", ".join(sorted(missing)))
    return 0


def cmd_check(a):
    import platform

    out = {"python": sys.version.split()[0], "platform": platform.platform()}
    try:
        import mujoco

        out["mujoco"] = mujoco.__version__
    except Exception as e:
        out["mujoco"] = f"MISSING ({e})"
    try:
        from .sim import SimEnv
        from .tasks import get_task

        env = SimEnv(get_task("lift"), 0)
        img = env.render("front")
        out["render"] = f"ok {img.shape}" if img is not None else f"FAILED ({env.render_error})"
        env.close()
    except Exception as e:
        out["render"] = f"FAILED ({type(e).__name__}: {e})"
    k = api_key()
    out["NEBIUS_API_KEY"] = f"set ({k[:4]}...{k[-2:]})" if k and len(k) > 8 else ("set" if k else "NOT SET")
    out["base_url"] = base_url()
    import shutil

    out["nebius_cli"] = shutil.which("nebius") or "not found (only needed for --backend nebius)"
    for mod in ("openai", "boto3", "mcp", "matplotlib"):
        try:
            __import__(mod)
            out[mod] = "installed"
        except Exception:
            out[mod] = "not installed"
    out["MUJOCO_GL"] = os.environ.get("MUJOCO_GL", "(default)")
    _print_json(out)
    return 0


def cmd_oracle(a):
    from .oracles import ORACLES
    from .runner import LocalRunner, run_inline
    from .stats import fmt_ci

    tasks = list(ORACLES) if a.task == "all" else [a.task]
    rc = 0
    for t in tasks:
        specs = [{"task": t, "seed": 500_000 + i, "code": ORACLES[t], "render": {"live": False, "keyframes": a.frames},
                  "realism": a.realism} for i in range(a.n)]
        out = Path(a.out) / f"oracle-{t}"
        t0 = time.time()
        res = run_inline(specs, out) if a.inline else LocalRunner(workers=a.workers).run_batch(specs, out)
        k = sum(bool(r.get("success_gt")) for r in res)
        errs = [f"{r['seed']}: {(r.get('error') or {}).get('type')}: {(r.get('error') or {}).get('message', '')[:100]}" for r in res if r.get("error")]
        print(f"{t:6s} reference fixture: {fmt_ci(k, a.n)}  ({time.time() - t0:.1f}s)")
        for e in errs[:5]:
            print("   error", e)
        if a.verbose:
            for r in res:
                if r.get("success_gt"):
                    continue
                print(f"   FAIL seed {r['seed']}: metrics {r.get('metrics')} halted={r.get('halted')}")
                print(f"        layout {r.get('layout')}")
                for tr in (r.get("trace") or [])[-6:]:
                    print(f"        t={tr.get('t')} {tr.get('call')} -> {json.dumps(tr.get('result', tr.get('error')), default=str)[:150]}")
        if k / max(1, a.n) < a.min:
            rc = 1
    return rc


def cmd_eval(a):
    from .runner import LocalRunner
    from .stats import fmt_ci

    code = Path(a.skill).read_text(encoding="utf-8")
    specs = [{"task": a.task, "seed": a.seed_base + i, "code": code, "render": {"live": False, "keyframes": False}} for i in range(a.n)]
    res = LocalRunner(workers=a.workers).run_batch(specs, Path(a.out))
    k = sum(bool(r.get("success_gt")) for r in res)
    print(fmt_ci(k, a.n))
    return 0


def cmd_learn(a):
    from .agent import LearnConfig, Learner

    cfg = LearnConfig(task=a.task, instruction=a.instruction, coder=a.coder, summarizer=a.summarizer, judge_model=a.judge,
                      reward=a.reward, rounds=a.rounds, episodes=a.n, eval_episodes=a.eval, target=a.target,
                      judge_mode=a.judge_mode, judge_thinking={"on": True, "off": False}.get(a.judge_think), use_library=a.library, probe=a.probe, backend=a.backend, workers=a.workers,
                      budget_usd=a.budget, run_id=a.run_id, runs_root=a.runs, mock=a.mock, seed_offset=a.seed_offset, realism=a.realism, select_episodes=a.select,
                      max_tokens=a.max_tokens)
    learner = Learner(cfg)
    print(f"run {learner.run_id} -> {learner.dir}")
    card = learner.run()
    ev = card.get("eval") or {}
    if ev:
        print(f"held-out success: {ev['k']}/{ev['n']} = {ev['p']:.0%} (95% CI {ev['lo']:.0%}-{ev['hi']:.0%}), "
              f"total ${card['receipt']['total_usd']:.4f}")
    print(f"skill card: {learner.dir / 'card.html'}")
    return 0


def cmd_pilot(a):
    from .experiments import pilot

    res = pilot(models=tuple(a.models.split(",")), rounds=a.rounds, episodes=a.n, eval_episodes=a.eval,
                budget_usd=a.budget, runs_root=a.runs, workers=a.workers, mock=a.mock, realism=a.realism)
    return 0 if res["gate_pass"] else 2


def cmd_exp(a):
    from . import experiments as ex

    if a.which == "scoreboard":
        _print_json(ex.scoreboard(models=tuple(a.models.split(",")), tasks=tuple(a.tasks.split(",")), rounds=a.rounds,
                                  episodes=a.n, eval_episodes=a.eval, budget_usd=a.budget, runs_root=a.runs, workers=a.workers, mock=a.mock,
                                  realism=a.realism)["table"])
    elif a.which == "ablation":
        _print_json(ex.ablation(tasks=tuple(a.tasks.split(",")), coder=a.coder, rounds=a.rounds, episodes=a.n,
                                eval_episodes=a.eval, budget_usd=a.budget, runs_root=a.runs, workers=a.workers, mock=a.mock,
                                realism=a.realism)["table"])
    elif a.which == "judge":
        res = ex.judge_eval(a.paths or [a.runs], n=a.n_judge, budget_usd=a.budget, out_root=a.runs)
        _print_json({k: v for k, v in res.items() if k != "rows"})
    elif a.which == "gain":
        ex.practice_gain(a.paths or [f"{a.runs}/**/*-gt*"], workers=a.workers, out_root=a.runs)
    elif a.which == "plots":
        for f in ex.plots(a.paths, a.out):
            print(f)
    return 0


def cmd_card(a):
    from .card import rebuild

    card = rebuild(a.run_dir)
    print(f"rebuilt card for {card['run_id']}")
    return 0


def cmd_ui(a):
    from .ui.server import serve

    serve(port=a.port, runs_root=a.runs, open_browser=not a.no_browser)
    return 0


def cmd_replay(a):
    from .replay import grid_gif

    src = Path(a.source)
    code_path = src / "best_skill.py" if src.is_dir() else src
    task = a.task
    if task is None and src.is_dir() and (src / "config.json").exists():
        task = json.loads((src / "config.json").read_text(encoding="utf-8"))["task"]
    if not task:
        print("--task is required when replaying a .py file")
        return 1
    realism = a.realism
    cfg = json.loads((src / "config.json").read_text(encoding="utf-8")) if src.is_dir() and (src / "config.json").exists() else {}
    if cfg and realism is None:
        realism = cfg.get("realism", "sim")
    realism = realism or "sim"
    if a.compare:
        from .agent import EVAL_SEED_BASE
        from .replay import compare_gif

        seeds = [int(s) for s in a.seeds.split(",")] if a.seeds else [EVAL_SEED_BASE + int(cfg.get("seed_offset", 0)) + i for i in range(a.n)]
        card = json.loads((src / "card.json").read_text(encoding="utf-8")) if (src / "card.json").exists() else {}
        res = compare_gif((src / "round_1" / "skill.py").read_text(encoding="utf-8"), code_path.read_text(encoding="utf-8"), task, seeds,
                          a.out, best_round=card.get("best_round"), realism=realism)
        _print_json(res)
        return 0
    seeds = [int(s) for s in a.seeds.split(",")] if a.seeds else list(range(200_000, 200_000 + a.n))
    res = grid_gif(code_path.read_text(encoding="utf-8"), task, seeds, a.out, cols=a.cols, realism=realism)
    _print_json(res)
    return 0


def cmd_nebius(a):
    from . import nebius

    if a.action == "hello":
        print("Creating a small PAID Serverless Job (cpu-d3 2vcpu-8gb, a few minutes)...")
        print("job:", nebius.hello())
        print("Follow with: nebius ai job logs <job id> --follow")
    elif a.action == "status":
        r = nebius.NebiusJobRunner("unused", "status")
        print(r.job_state(a.job))
    elif a.action == "logs":
        print(nebius._cli(["ai", "job", "logs", a.job, "--tail", "200"], check=False))
    return 0


def cmd_mcp(a):
    from .mcp_server import main as mcp_main

    return mcp_main(task=a.task, seed=a.seed)


def cmd_library(a):
    from .library import SkillLibrary

    for e in SkillLibrary().entries():
        p = e.get("success")
        ptxt = "n/a" if p is None else f"{p:.0%}"
        coder = e.get("coder")
        ctxt = coder.get("alias") if isinstance(coder, dict) else str(coder)
        usd = e.get("usd") or 0.0
        print(f"{e['task']:7s} {e['run_id']:45s} success {ptxt}  coder {ctxt}  ${usd:.3f}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="knack", description="Robots that learn skills by practising in simulation. Zero demonstrations.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("tasks", help="list scenes").set_defaults(fn=cmd_tasks)
    p = sub.add_parser("models", help="model catalogue (and --remote: list models your key can see; free)")
    p.add_argument("--remote", action="store_true")
    p.set_defaults(fn=cmd_models)
    sub.add_parser("check", help="environment diagnostics (MuJoCo, rendering, key, CLIs)").set_defaults(fn=cmd_check)

    p = sub.add_parser("oracle", help="run the hand-written reference fixtures (sim sanity check, no LLM)")
    p.add_argument("task", nargs="?", default="all")
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--workers", type=int)
    p.add_argument("--inline", action="store_true")
    p.add_argument("--frames", action="store_true")
    p.add_argument("--verbose", "-v", action="store_true", help="print metrics and the last robot calls of failed seeds")
    p.add_argument("--min", type=float, default=1.0, help="exit non-zero if any scene's success is below this")
    p.add_argument("--out", default="runs/_oracle")
    p.add_argument("--realism", default="sim", choices=["sim", "real"])
    p.set_defaults(fn=cmd_oracle)

    p = sub.add_parser("eval", help="evaluate a skill file on held-out layouts (ground truth)")
    p.add_argument("skill")
    p.add_argument("task")
    p.add_argument("--n", type=int, default=100)
    p.add_argument("--seed-base", type=int, default=300_000)
    p.add_argument("--workers", type=int)
    p.add_argument("--out", default="runs/_eval")
    p.set_defaults(fn=cmd_eval)

    def learn_args(p):
        p.add_argument("--rounds", type=int, default=4)
        p.add_argument("--select", type=int, default=16, help="fresh layouts used to re-check the top practice versions (0 = off)")
        p.add_argument("--realism", default="sim", choices=["sim", "real"],
                       help="real = camera-grade perception noise (~8 mm) and wider mass/friction/grip randomisation")
        p.add_argument("--n", type=int, default=8, help="parallel practice episodes per round")
        p.add_argument("--eval", type=int, default=100, help="held-out evaluation episodes")
        p.add_argument("--budget", type=float, default=1.0, help="hard USD cap for this command")
        p.add_argument("--workers", type=int)
        p.add_argument("--runs", default="runs")
        p.add_argument("--mock", action="store_true", help="offline plumbing test with a canned coder (no tokens)")

    p = sub.add_parser("learn", help="practise a task and produce a skill card")
    p.add_argument("task")
    p.add_argument("--instruction", help="custom instruction for the scene (forces --reward vlm)")
    p.add_argument("--coder", default="ultra")
    p.add_argument("--summarizer", default="lightning")
    p.add_argument("--judge", default="super-vl")
    p.add_argument("--reward", default="gt", choices=["gt", "vlm", "self"])
    p.add_argument("--judge-mode", default="auto", choices=["auto", "always", "never"])
    p.add_argument("--judge-think", default="default", choices=["default", "on", "off"],
                   help="Nemotron reasoning trace for the vision judge (off = cheaper and faster)")
    p.add_argument("--target", type=float, default=0.9)
    p.add_argument("--library", action="store_true", help="offer verified skills from the library to the coder")
    p.add_argument("--probe", action="store_true", help="let the coder explore with tool calls first")
    p.add_argument("--backend", default="local", choices=["local", "nebius"])
    p.add_argument("--run-id")
    p.add_argument("--seed-offset", type=int, default=0)
    p.add_argument("--max-tokens", type=int, default=16000)
    learn_args(p)
    p.set_defaults(fn=cmd_learn)

    p = sub.add_parser("pilot", help="day-1 gate: Super vs Ultra on lift/place/push")
    p.add_argument("--models", default="super,ultra")
    learn_args(p)
    p.set_defaults(fn=cmd_pilot, budget=0.9, eval=50)

    p = sub.add_parser("exp", help="experiments: scoreboard | ablation | judge | plots")
    p.add_argument("which", choices=["scoreboard", "ablation", "judge", "plots", "gain"])
    p.add_argument("paths", nargs="*")
    p.add_argument("--models", default="nano,super,ultra,deepseek-flash")
    p.add_argument("--tasks", default="lift,place,push,stack,tray")
    p.add_argument("--coder", default="super")
    p.add_argument("--n-judge", type=int, default=100)
    p.add_argument("--out", default="docs/figures")
    learn_args(p)
    p.set_defaults(fn=cmd_exp)

    p = sub.add_parser("card", help="re-render a run's skill card")
    p.add_argument("run_dir")
    p.set_defaults(fn=cmd_card)

    p = sub.add_parser("ui", help="open the Knack console")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--runs", default="runs")
    p.add_argument("--no-browser", action="store_true")
    p.set_defaults(fn=cmd_ui)

    p = sub.add_parser("replay", help="GIF of a skill on a grid of layouts (for videos)")
    p.add_argument("source", help="run directory or skill .py")
    p.add_argument("--task")
    p.add_argument("--seeds")
    p.add_argument("--n", type=int, default=9)
    p.add_argument("--cols", type=int)
    p.add_argument("--out", default="replay.gif")
    p.add_argument("--realism", choices=["sim", "real"], help="default: the run's own setting")
    p.add_argument("--compare", action="store_true", help="two rows on the same held-out layouts: round 1 vs the practised version")
    p.set_defaults(fn=cmd_replay)

    p = sub.add_parser("nebius", help="Nebius Serverless Jobs helpers (PAID)")
    p.add_argument("action", choices=["hello", "status", "logs"])
    p.add_argument("job", nargs="?")
    p.set_defaults(fn=cmd_nebius)

    p = sub.add_parser("mcp", help="serve the robot tools over MCP (stdio)")
    p.add_argument("--task", default="lift")
    p.add_argument("--seed", type=int, default=0)
    p.set_defaults(fn=cmd_mcp)

    sub.add_parser("library", help="list verified skills").set_defaults(fn=cmd_library)
    return ap


def main(argv=None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    return int(args.fn(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
