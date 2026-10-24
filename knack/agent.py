"""The Knack practice loop.

write skill -> practise on N random layouts in parallel -> score (ground truth,
vision judge, or self-report) -> summarise failures -> rewrite skill -> ...
-> evaluate the best version on held-out layouts -> skill card.
"""
from __future__ import annotations

import datetime as _dt
import difflib
import json
import os
import re
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

from . import prompts
from .config import ROLE_DEFAULTS, resolve_model
from .judge import VLMJudge
from .library import SkillLibrary
from .llm import BudgetExceeded, Ledger, LLMClient, MockLLM
from .sandbox import extract_code, validate
from .stats import judge_metrics, wilson
from .tasks import get_task

TRAIN_SEED_BASE = 1000
SELECT_SEED_BASE = 50_000  # fresh layouts used only to choose between candidate versions
EVAL_SEED_BASE = 100_000


@dataclass
class LearnConfig:
    task: str
    instruction: str | None = None
    coder: str = ROLE_DEFAULTS["coder"]
    summarizer: str = ROLE_DEFAULTS["summarizer"]
    judge_model: str = ROLE_DEFAULTS["judge"]
    reward: str = "gt"  # gt | vlm | self
    rounds: int = 4
    episodes: int = 8
    eval_episodes: int = 100
    target: float = 0.9
    judge_mode: str = "auto"  # auto (judge when reward=vlm) | always | never
    judge_threshold: float = 0.6
    judge_eval_episodes: int = 20
    judge_thinking: bool | None = None  # None = model default; False = no reasoning trace (cheaper, faster)
    use_library: bool = False
    probe: bool = False
    backend: str = "local"
    workers: int | None = None
    budget_usd: float | None = 1.0
    run_id: str | None = None
    runs_root: str = "runs"
    max_tokens: int = 16000
    temperature: float = 0.2
    seed_offset: int = 0
    save_to_library: bool = True
    library_min_success: float = 0.5
    mock: bool = False
    live_eval_tiles: int = 16
    realism: str = "sim"  # sim | real (camera-grade noise, wider physics randomisation)
    select_episodes: int = 16  # re-check the top practice versions on fresh layouts before the final eval (gt only)

    def to_dict(self) -> dict:
        return asdict(self)


def _now() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def parse_notes(text: str) -> str:
    m = re.search(r"<notes>(.*?)</notes>", text, flags=re.S | re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r"(?:^|\n)#*\s*notes?:?\s*\n(.*?)(?:```|$)", text, flags=re.S | re.I)
    return m.group(1).strip()[:2000] if m else ""


def _fmt_err(r: dict) -> str:
    e = r.get("error")
    if not e:
        return ""
    tb = (e.get("traceback") or "").strip().splitlines()
    where = ""
    for line in tb:
        if line.strip().startswith("skill.py line"):
            where = line.strip()
    msg = f"{e.get('type')}: {e.get('message', '')}".strip()
    return f"{msg[:220]}" + (f" [{where[:160]}]" if where else "")


def _obj_brief(obs: dict) -> str:
    if not obs:
        return ""
    parts = []
    for n, o in (obs.get("objects") or {}).items():
        p = o.get("pos", [0, 0, 0])
        parts.append(f"{n} at ({p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f})")
    g = obs.get("gripper") or {}
    parts.append(f"gripper holding {g.get('holding')}")
    return "; ".join(parts)


class Learner:
    def __init__(self, cfg: LearnConfig, *, responder=None, runner=None, llm=None):
        self.cfg = cfg
        self.task = get_task(cfg.task)
        self.instruction = (cfg.instruction or self.task.instruction).strip()
        self.custom = self.instruction != self.task.instruction
        if cfg.reward not in ("gt", "vlm", "self"):
            raise ValueError("reward must be gt, vlm or self")
        if self.custom and cfg.reward == "gt":
            raise ValueError("a custom instruction has no ground-truth check; use --reward vlm")
        run_id = cfg.run_id or f"{_now()}-{cfg.task}-{_slug(cfg.coder)}-{cfg.reward}" + ("-real" if cfg.realism == "real" else "")
        self.run_id = run_id
        self.dir = Path(cfg.runs_root) / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ledger = Ledger(self.dir / "ledger.jsonl", budget_usd=cfg.budget_usd)
        if llm is not None:
            self.llm = llm
            self.llm.ledger = self.ledger
        elif responder is not None or cfg.mock:
            self.llm = MockLLM(self.ledger, responder or _default_mock_responder(self.task.id))
        else:
            self.llm = LLMClient(self.ledger)
        self.runner = runner or make_runner(cfg, self.ledger, self.dir)
        self.judge_enabled = cfg.judge_mode == "always" or (cfg.judge_mode == "auto" and (cfg.reward == "vlm" or self.custom))
        if cfg.judge_mode == "never" and cfg.reward == "vlm":
            raise ValueError("reward=vlm needs the judge")
        self.judge = VLMJudge(self.llm, cfg.judge_model, cfg.judge_threshold, thinking=cfg.judge_thinking) if self.judge_enabled else None
        self.notes = ""
        self.history: list[str] = []
        self.rounds: list[dict] = []
        self.codes: list[str] = []
        self.best: dict | None = None
        self.candidates: list[dict] = []
        self.selection: dict | None = None
        self.eval: dict | None = None
        self.started = time.time()
        self.state = {
            "run_id": run_id, "task": self.task.id, "title": self.task.title, "instruction": self.instruction,
            "custom_instruction": self.custom, "reward": cfg.reward, "realism": cfg.realism, "status": "starting", "phase": "starting",
            "round": 0, "rounds_max": cfg.rounds, "n": cfg.episodes, "episodes": [], "rounds": [], "eval": None,
            "models": self._model_chips(), "cost": {}, "backend": getattr(self.runner, "name", cfg.backend),
            "mock": bool(cfg.mock or responder is not None), "started": time.time(), "error": None,
        }

    # ------------------------------------------------------------------ state
    def _model_chips(self) -> dict:
        out = {}
        for role, name in (("coder", self.cfg.coder), ("summarizer", self.cfg.summarizer), ("judge", self.cfg.judge_model)):
            if role == "judge" and not getattr(self, "judge_enabled", True):
                continue
            m = resolve_model(name)
            out[role] = {"alias": m.alias, "id": m.id, "nvidia": m.nvidia}
        return out

    def _set(self, **kw):
        self.state.update(kw)
        self.state["updated"] = time.time()
        self.state["elapsed"] = round(time.time() - self.started, 1)
        s = self.ledger.summary()
        self.state["cost"] = {"llm_usd": s["llm_usd"], "compute_usd": s["compute_usd"], "total_usd": s["total_usd"], "by_role": s["by_role"]}
        from .fsutil import atomic_write_text

        # best-effort: the console may be reading state.json (Windows refuses to replace an open file)
        atomic_write_text(self.dir / "state.json", json.dumps(self.state, indent=1, default=str), best_effort=True)

    def _event(self, kind: str, **data):
        with (self.dir / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"t": round(time.time(), 2), "kind": kind, **data}, default=str) + "\n")

    def _save_llm(self, name: str, messages: list, reply_text: str, reasoning: str = ""):
        d = self.dir / "llm"
        d.mkdir(exist_ok=True)
        slim = []
        for m in messages:
            c = m["content"]
            if isinstance(c, list):
                c = [x if x.get("type") == "text" else {"type": x.get("type"), "omitted": True} for x in c]
            slim.append({"role": m["role"], "content": c})
        (d / f"{name}.json").write_text(json.dumps({"messages": slim, "reply": reply_text, "reasoning": reasoning[:20000]}, indent=1), encoding="utf-8")

    # ------------------------------------------------------------------ helpers
    def _train_seeds(self, k: int) -> list:
        return [TRAIN_SEED_BASE * k + self.cfg.seed_offset + i for i in range(self.cfg.episodes)]

    def _example_obs(self) -> dict:
        from .robot import SimRobot
        from .sim import SimEnv

        env = SimEnv(self.task, TRAIN_SEED_BASE + self.cfg.seed_offset, render_size=(64, 48))
        obs = SimRobot(env, obs_noise=0.0).snapshot(noisy=False)
        env.close()
        return obs

    def _coder(self, name: str, messages: list) -> tuple[str | None, str]:
        reply = self.llm.chat("coder", self.cfg.coder, messages, temperature=self.cfg.temperature, max_tokens=self.cfg.max_tokens)
        self._save_llm(name, messages, reply.text, reply.reasoning)
        code = extract_code(reply.text)
        if code is None:
            messages = messages + [{"role": "assistant", "content": reply.text[:4000]}, {"role": "user", "content": prompts.FORMAT_REMINDER}]
            reply = self.llm.chat("coder", self.cfg.coder, messages, temperature=self.cfg.temperature, max_tokens=self.cfg.max_tokens)
            self._save_llm(name + "_retry", messages, reply.text, reply.reasoning)
            code = extract_code(reply.text)
        notes = parse_notes(reply.text)
        return code, notes

    def _ensure_valid(self, code: str, k: int) -> str:
        for attempt in range(2):
            problems = validate(code)
            if not problems:
                return code
            self._set(phase=f"fixing code (rejected: {problems[0][:80]})")
            self._event("compile_error", round=k, problems=problems)
            msgs = [{"role": "system", "content": prompts.CODER_SYSTEM},
                    {"role": "user", "content": prompts.compile_error_user("; ".join(problems[:6])) + "\n\n```python\n" + code + "\n```"}]
            new, notes = self._coder(f"round_{k}_compile_fix_{attempt + 1}", msgs)
            if new:
                code = new
            if notes:
                self.notes = notes
        return code

    # ------------------------------------------------------------------ episodes
    def _on_episode(self, event: str, seed: int, result):
        for e in self.state["episodes"]:
            if e["seed"] == seed:
                e["status"] = "running" if event == "running" else "done"
                if result is not None:
                    e["success_gt"] = None if self.custom else bool(result.get("success_gt"))
                    e["self_report"] = result.get("self_report")
                    e["error"] = _fmt_err(result)[:160] or None
                    e["frames"] = result.get("frames", {})
                break
        self._set()

    def _run_batch(self, code: str, seeds: list, out: Path, live_tiles: int | None = None) -> list:
        specs = []
        for i, s in enumerate(seeds):
            live = live_tiles is None or i < live_tiles
            specs.append({"task": self.task.id, "seed": s, "code": code, "max_time": self.task.max_time,
                          "render": {"live": live, "keyframes": True}, "realism": self.cfg.realism})
        before = getattr(self.runner, "compute_seconds", 0.0)
        results = self.runner.run_batch(specs, out, on_update=self._on_episode)
        spent = getattr(self.runner, "compute_seconds", 0.0) - before
        usd = getattr(self.runner, "last_batch_usd", 0.0) or 0.0
        self.ledger.add_compute(getattr(self.runner, "name", "local"), spent, usd, {"episodes": len(seeds)})
        return results

    def _judge_all(self, results: list, ep_root: Path, limit: int | None = None):
        todo = results if limit is None else results[:limit]

        def one(r):
            v = self.judge.judge(self.instruction, r.get("frames") or {}, ep_root / f"ep_{r['seed']}")
            r["judge"] = v.to_dict()
            return r

        with ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(one, todo))
        for r in todo:
            for e in self.state["episodes"]:
                if e["seed"] == r["seed"]:
                    e["judge"] = {k: r["judge"][k] for k in ("success", "confidence", "reason", "abstained")}
        self._set()

    def _reward(self, r: dict) -> bool:
        if self.cfg.reward == "gt":
            return bool(r.get("success_gt"))
        if self.cfg.reward == "vlm":
            return bool((r.get("judge") or {}).get("success") is True)
        return r.get("self_report") is True

    def _episode_line(self, r: dict) -> str:
        reward = self.cfg.reward
        ok = r["reward"]
        if reward == "vlm":
            j = r.get("judge") or {}
            if j.get("abstained"):
                head = f"seed {r['seed']}: uncertain (judge abstained: {j.get('reason', '')[:100]})"
            else:
                head = f"seed {r['seed']}: {'SUCCESS' if ok else 'FAIL'} (judge, confidence {j.get('confidence', 0):.2f}: {j.get('reason', '')[:120]})"
        elif reward == "self":
            head = f"seed {r['seed']}: {'SUCCESS' if ok else 'FAIL'} (returned {r.get('returned', 'nothing')})"
        else:
            head = f"seed {r['seed']}: {'SUCCESS' if ok else 'FAIL'}"
        parts = [head]
        err = _fmt_err(r)
        if err:
            parts.append(f"error: {err}")
        if r.get("halted"):
            parts.append(f"halted: {r['halted'][:120]}")
        if reward == "gt" and r.get("metrics"):
            parts.append("check: " + ", ".join(f"{k}={v}" for k, v in r["metrics"].items()))
        if reward in ("gt", "vlm") and r.get("final_obs"):
            parts.append("final: " + _obj_brief(r["final_obs"]))
        sc = r.get("safety_summary") or {}
        if sc.get("clamp"):
            parts.append(f"safety clamps: {sc['clamp']}")
        return " | ".join(parts)

    def _traces(self, results: list, max_eps: int, tail: int) -> str:
        failed = [r for r in results if not r["reward"]]
        seen, picked = set(), []
        for r in failed:  # prefer diverse error types
            key = (r.get("error") or {}).get("type")
            if key not in seen:
                picked.append(r)
                seen.add(key)
        for r in failed:
            if len(picked) >= max_eps:
                break
            if r not in picked:
                picked.append(r)
        out = []
        for r in picked[:max_eps]:
            lines = [f"--- seed {r['seed']} ---"]
            e = r.get("error")
            if e and e.get("traceback"):
                lines.append(e["traceback"])
            tr = r.get("trace") or []
            if len(tr) > tail:
                lines.append(f"(first {len(tr) - tail} calls omitted)")
            for t in tr[-tail:]:
                s = f"t={t.get('t')} {t.get('call')}"
                if "result" in t:
                    s += f" -> {json.dumps(t['result'], default=str)[:160]}"
                if "error" in t:
                    s += f" !! {t['error'][:200]}"
                lines.append(s)
            if r.get("printed"):
                lines.append("printed: " + " / ".join(r["printed"][-5:])[:400])
            out.append("\n".join(lines))
        return "\n".join(out)

    # ------------------------------------------------------------------ loop phases
    def _initial_code(self) -> str:
        self._set(status="running", phase="reading the scene")
        example = self._example_obs()
        lib = []
        if self.cfg.use_library:
            lib = SkillLibrary().retrieve(self.instruction, exclude_task=self.task.id)
            self._event("library", skills=[e["task"] for e in lib])
        probe_log = None
        if self.cfg.probe:
            from .probe import run_probe

            self._set(phase="exploring with tools")
            probe_log = run_probe(self.llm, self.cfg.coder, self.task, self.instruction, TRAIN_SEED_BASE + self.cfg.seed_offset, self.dir)
        self._set(phase="writing skill v1")
        first = prompts.first_user(self.instruction, self.task.title, example, lib, probe_log)
        if self.cfg.realism == "real":
            first = prompts.REAL_PERCEPTION_NOTE + "\n\n" + first
        msgs = [{"role": "system", "content": prompts.CODER_SYSTEM}, {"role": "user", "content": first}]
        code, notes = self._coder("round_1_write", msgs)
        if notes:
            self.notes = notes
        if code is None:
            raise RuntimeError("the coder did not return code for the first version")
        return code

    def _practice(self, k: int, code: str) -> dict:
        rdir = self.dir / f"round_{k}"
        rdir.mkdir(exist_ok=True)
        (rdir / "skill.py").write_text(code, encoding="utf-8")
        prev = self.codes[-1] if self.codes else ""
        diff = "".join(difflib.unified_diff(prev.splitlines(True), code.splitlines(True), f"round_{k - 1}/skill.py", f"round_{k}/skill.py"))
        (rdir / "diff.patch").write_text(diff, encoding="utf-8")
        (rdir / "notes.md").write_text(self.notes or "", encoding="utf-8")
        self.codes.append(code)
        seeds = self._train_seeds(k)
        self._set(phase=f"practising round {k}", round=k,
                  episodes=[{"seed": s, "status": "queued", "dir": f"round_{k}/episodes/ep_{s}"} for s in seeds])
        t0 = time.time()
        results = self._run_batch(code, seeds, rdir / "episodes")
        if self.judge:
            self._set(phase=f"judging round {k}")
            self._judge_all(results, rdir / "episodes")
        for r in results:
            r["reward"] = self._reward(r)
        n_ok = sum(r["reward"] for r in results)
        rec = {
            "round": k, "n": len(results), "k": n_ok, "success": n_ok / max(1, len(results)),
            "gt_k": None if self.custom else sum(bool(r.get("success_gt")) for r in results),
            "self_k": sum(r.get("self_report") is True for r in results),
            "errors": sum(1 for r in results if r.get("error")),
            "wall_s": round(time.time() - t0, 1), "usd_cum": round(self.ledger.total_usd(), 5),
            "code": f"round_{k}/skill.py", "diff": f"round_{k}/diff.patch", "lines": code.count("\n") + 1,
            "notes": (self.notes or "")[:1500],
        }
        if self.judge and not self.custom:
            rec["judge"] = judge_metrics([(bool(r.get("success_gt")), (r.get("judge") or {}).get("success")) for r in results])
        compact = [{"seed": r["seed"], "reward": r["reward"], "success_gt": r.get("success_gt"), "self_report": r.get("self_report"),
                    "judge": r.get("judge"), "error": r.get("error"), "metrics": r.get("metrics"), "frames": r.get("frames")} for r in results]
        (rdir / "round.json").write_text(json.dumps({**rec, "episodes": compact}, indent=1, default=str), encoding="utf-8")
        self.rounds.append(rec)
        self._set(rounds=self.rounds)
        self._event("round", **{k2: v for k2, v in rec.items() if k2 != "notes"})
        return {"record": rec, "results": results}

    def _summarize(self, k: int, code: str, rnd: dict) -> str:
        results = rnd["results"]
        if all(r["reward"] for r in results):
            return ""
        self._set(phase=f"summarising failures (round {k})")
        lines = [self._episode_line(r) for r in results]
        msgs = [{"role": "system", "content": prompts.SUMMARIZER_SYSTEM},
                {"role": "user", "content": prompts.summarizer_user(self.instruction, code, lines, self._traces(results, 6, 30))}]
        try:
            # thinking off: the summary is a short structured readout, and with thinking on Lightning
            # spent its whole 4000-token budget reasoning and returned no answer (live run, 23 Oct 2026)
            reply = self.llm.chat("summarizer", self.cfg.summarizer, msgs, temperature=0.1, max_tokens=1500, thinking=False)
            text = reply.text.strip() or "(summariser returned no answer)"
            self._save_llm(f"round_{k}_summary", msgs, text, reply.reasoning)
        except BudgetExceeded:
            raise
        except Exception as e:  # the summary is helpful, not essential
            text = f"(summariser unavailable: {type(e).__name__})"
        (self.dir / f"round_{k}" / "summary.md").write_text(text, encoding="utf-8")
        self.rounds[-1]["summary"] = text[:2000]
        self._set(rounds=self.rounds)
        return text

    def _regression_note(self, k: int, score: float, best: dict, bad_code: str) -> str:
        diff = "".join(difflib.unified_diff(best["code"].splitlines(True), bad_code.splitlines(True),
                                            f"round_{best['round']}/skill.py (best)", f"round_{k}/skill.py (worse)"))
        if len(diff) > 3500:
            diff = diff[:3500] + "\n... (diff truncated)"
        return (f"REGRESSION: your round {k} version scored {score:.0%}, worse than round {best['round']} "
                f"({best['score']:.0%}). It has been discarded. The outcomes and analysis below are from the discarded "
                f"version; the 'Current code' is the round {best['round']} version you are editing again. "
                f"This change made things worse, do not repeat it:\n{diff}")

    def _revise(self, k: int, code: str, rnd: dict, summary: str, regression: str | None = None) -> str:
        self._set(phase=f"rewriting skill (v{k + 1})" + (" from the best version" if regression else ""))
        results = rnd["results"]
        rec = rnd["record"]
        lines = [self._episode_line(r) for r in results]
        self.history.append(f"round {k}: {rec['k']}/{rec['n']} success, {rec['errors']} episodes raised errors"
                            + (f" (worse than round {rec.get('reverted_to')}: reverted)" if regression else ""))
        user = prompts.revise_user(self.instruction, k, self.cfg.reward, rec["k"], rec["n"], lines, summary,
                                   self._traces(results, 2, 25), self.notes, self.history[:-1], code)
        if regression:
            user = regression + "\n\n" + user
        msgs = [{"role": "system", "content": prompts.CODER_SYSTEM}, {"role": "user", "content": user}]
        new, notes = self._coder(f"round_{k + 1}_rewrite", msgs)
        if notes:
            self.notes = notes
        if new is None:
            self._event("no_code", round=k)
            return code
        return new

    def _select_best(self):
        """Practice scores come from 8 layouts and are noisy (live, 23 Oct 2026: Ultra's 'best' round scored 88% in
        practice and exactly the same as round 1 on held-out). Re-check the top versions on fresh layouts and keep
        the one with the most successes overall. Simulator check only, so it costs compute, not tokens."""
        n = self.cfg.select_episodes
        if n <= 0 or self.cfg.reward != "gt" or self.custom:
            return
        uniq, seen = [], set()
        for c in sorted(self.candidates, key=lambda c: (-c["k"] / max(1, c["n"]), c["round"])):
            if c["code"] not in seen:
                uniq.append(c)
                seen.add(c["code"])
        top = uniq[:3]
        if len(top) < 2:
            return
        self._set(phase=f"re-checking the top {len(top)} versions on {n} fresh layouts")
        seeds = [SELECT_SEED_BASE + self.cfg.seed_offset + i for i in range(n)]
        rows = []
        for c in top:
            res = self._run_batch(c["code"], seeds, self.dir / "select" / f"round_{c['round']}", live_tiles=0)
            ks = sum(bool(r.get("success_gt")) for r in res)
            rows.append({"round": c["round"], "practice": f"{c['k']}/{c['n']}", "recheck": f"{ks}/{n}",
                         "total_k": c["k"] + ks, "total_n": c["n"] + n, "code": c["code"]})
        best = max(rows, key=lambda r: (r["total_k"] / r["total_n"], -r["round"]))
        prev = self.best["round"]
        self.best = {"code": best["code"], "score": best["total_k"] / best["total_n"], "round": best["round"]}
        self.selection = {"episodes": n, "previous_choice": prev, "chosen": best["round"],
                          "rows": [{k: v for k, v in r.items() if k != "code"} for r in rows]}
        (self.dir / "select").mkdir(exist_ok=True)
        (self.dir / "select" / "selection.json").write_text(json.dumps(self.selection, indent=1), encoding="utf-8")
        self._event("selection", **self.selection)
        self._set(selection=self.selection)

    def _final_eval(self):
        best = self.best
        n = self.cfg.eval_episodes
        if not best or n <= 0:
            return None
        self._set(phase=f"evaluating on {n} held-out layouts",
                  episodes=[{"seed": EVAL_SEED_BASE + self.cfg.seed_offset + i, "status": "queued",
                             "dir": f"eval/episodes/ep_{EVAL_SEED_BASE + self.cfg.seed_offset + i}"}
                            for i in range(min(n, self.cfg.live_eval_tiles))])
        seeds = [EVAL_SEED_BASE + self.cfg.seed_offset + i for i in range(n)]
        root = self.dir / "eval" / "episodes"
        (self.dir / "eval").mkdir(exist_ok=True)
        (self.dir / "eval" / "skill.py").write_text(best["code"], encoding="utf-8")
        results = self._run_batch(best["code"], seeds, root, live_tiles=self.cfg.live_eval_tiles)
        source = "gt"
        jm = None
        if self.judge:
            limit = n if self.custom else min(n, self.cfg.judge_eval_episodes)
            self._set(phase=f"judging {limit} held-out episodes")
            try:
                self._judge_all(results, root, limit=limit)
            except BudgetExceeded:
                pass
            judged = [r for r in results[:limit] if r.get("judge")]
            if not self.custom and judged:
                jm = judge_metrics([(bool(r.get("success_gt")), r["judge"].get("success")) for r in judged])
        if self.custom:
            source = "vlm"
            k = sum(1 for r in results if (r.get("judge") or {}).get("success") is True)
        else:
            k = sum(1 for r in results if r.get("success_gt"))
        p, lo, hi = wilson(k, n)
        fails = [r for r in results if not ((r.get("judge") or {}).get("success") if self.custom else r.get("success_gt"))]
        gallery = []
        for r in fails[:8]:
            gallery.append({"seed": r["seed"], "error": _fmt_err(r)[:200], "metrics": r.get("metrics"),
                            "frame": f"eval/episodes/ep_{r['seed']}/{(r.get('frames') or {}).get('end_front', '')}"
                            if (r.get("frames") or {}).get("end_front") else None})
        ev = {"n": n, "k": k, "p": p, "lo": lo, "hi": hi, "source": source, "best_round": best["round"],
              "errors": sum(1 for r in results if r.get("error")),
              "halts": sum(1 for r in results if r.get("halted")),
              "safety_clamps": sum((r.get("safety_summary") or {}).get("clamp", 0) for r in results),
              "mean_sim_time": round(sum(r.get("sim_time") or 0 for r in results) / max(1, n), 2),
              "self_report_true": sum(r.get("self_report") is True for r in results),
              "judge": jm, "failures": gallery}
        compact = [{"seed": r["seed"], "success_gt": r.get("success_gt"), "self_report": r.get("self_report"), "judge": r.get("judge"),
                    "error": r.get("error"), "metrics": r.get("metrics"), "frames": r.get("frames")} for r in results]
        (self.dir / "eval" / "eval.json").write_text(json.dumps({**ev, "episodes": compact}, indent=1, default=str), encoding="utf-8")
        self.eval = ev
        self._set(eval=ev)
        return ev

    # ------------------------------------------------------------------ main
    def run(self) -> dict:
        from .card import write_card

        (self.dir / "config.json").write_text(json.dumps({**self.cfg.to_dict(), "run_id": self.run_id, "instruction": self.instruction}, indent=1), encoding="utf-8")
        status = "done"
        try:
            try:
                code = self._initial_code()
                for k in range(1, self.cfg.rounds + 1):
                    code = self._ensure_valid(code, k)
                    rnd = self._practice(k, code)
                    score = rnd["record"]["success"]
                    prev_best = self.best
                    regressed = prev_best is not None and score < prev_best["score"]
                    if self.best is None or score >= self.best["score"]:
                        self.best = {"code": code, "score": score, "round": k}
                    self.candidates.append({"round": k, "code": code, "k": rnd["record"]["k"], "n": rnd["record"]["n"]})
                    if score >= self.cfg.target or k == self.cfg.rounds:
                        break
                    summary = self._summarize(k, code, rnd)
                    if regressed:
                        # Keep what works: a rewrite that scores worse is discarded and the next rewrite
                        # starts again from the best version. Seen live on 23 Oct 2026: Ultra on push went
                        # 88% -> 0% -> 0% -> 0% by repeatedly editing its own broken rewrite.
                        note = self._regression_note(k, score, prev_best, code)
                        rnd["record"]["reverted_to"] = prev_best["round"]
                        self._event("revert", round=k, to_round=prev_best["round"], score=score, best=prev_best["score"])
                        code = self._revise(k, prev_best["code"], rnd, summary, regression=note)
                    else:
                        code = self._revise(k, code, rnd, summary)
            except BudgetExceeded as e:
                status = "stopped (budget)"
                self._event("budget", message=str(e))
            if self.best:
                try:
                    self._select_best()
                except BudgetExceeded:
                    pass
                (self.dir / "best_skill.py").write_text(self.best["code"], encoding="utf-8")
                self._final_eval()
        except Exception as e:
            status = "failed"
            self.state["error"] = f"{type(e).__name__}: {e}"
            self._event("error", message=str(e), tb=traceback.format_exc()[-3000:])
            self._set(status=status, phase="failed")
            raise
        self._set(phase="writing skill card", status=status)
        card = write_card(self)
        if status == "done" and self.cfg.save_to_library and self.eval and (self.eval["p"] >= self.cfg.library_min_success) and not self.state.get("mock"):
            SkillLibrary().add(self.task.id, self.instruction, self.best["code"], card, self.dir)
            card["saved_to_library"] = True
        self._set(status=status, phase="done", card="card.json")
        return card


def make_runner(cfg: LearnConfig, ledger: Ledger, run_dir: Path):
    if cfg.backend == "local":
        from .runner import LocalRunner

        return LocalRunner(workers=cfg.workers)
    if cfg.backend == "nebius":
        from .nebius import NebiusJobRunner

        return NebiusJobRunner.from_env(run_id=run_dir.name)
    raise ValueError(f"unknown backend {cfg.backend}")


def _default_mock_responder(task_id: str):
    """Offline plumbing test: v1 is deliberately broken, v2 is the reference fixture.

    This exercises every part of the pipeline without tokens. It is NOT learning.
    """
    from .oracles import BROKEN, ORACLES

    state = {"coder_calls": 0}

    def respond(role, messages):
        if role == "coder":
            state["coder_calls"] += 1
            code = BROKEN if state["coder_calls"] == 1 else ORACLES[task_id]
            return f"<notes>\n- mock coder call {state['coder_calls']}\n</notes>\n```python\n{code.strip()}\n```"
        if role == "summarizer":
            return "Mock summary: the gripper never closes around the object; descend to the object centre before grasping."
        if role == "judge":
            return '{"success": false, "confidence": 0.5, "reason": "mock judge"}'
        return ""

    return respond
