"""Skill card: the deliverable of a Knack run (JSON + Markdown + standalone HTML)."""
from __future__ import annotations

import html
import json
import time
from pathlib import Path

from .config import resolve_model


def _pct(x):
    return "n/a" if x is None else f"{x:.0%}"


def build_card(learner) -> dict:
    cfg = learner.cfg
    led = learner.ledger.summary()
    ev = learner.eval or {}
    models = {}
    for role, name in (("coder", cfg.coder), ("summarizer", cfg.summarizer), ("judge", cfg.judge_model)):
        if role == "judge" and not learner.judge_enabled:
            continue
        m = resolve_model(name)
        use = led["by_role"].get(role, {})
        models[role] = {"alias": m.alias, "id": m.id, "nvidia": m.nvidia, "calls": use.get("calls", 0),
                        "prompt_tokens": use.get("prompt_tokens", 0), "completion_tokens": use.get("completion_tokens", 0),
                        "usd": use.get("usd", 0.0), "price_in": m.price_in, "price_out": m.price_out}
    return {
        "run_id": learner.run_id,
        "task": learner.task.id,
        "title": learner.task.title,
        "instruction": learner.instruction,
        "custom_instruction": learner.custom,
        "reward": cfg.reward,
        "realism": getattr(cfg, "realism", "sim"),
        "status": learner.state.get("status"),
        "mock": learner.state.get("mock", False),
        "demonstrations": 0,
        "rounds": [{k: v for k, v in r.items() if k not in ("notes",)} for r in learner.rounds],
        "best_round": (learner.best or {}).get("round"),
        "eval": ev,
        "models": models,
        "receipt": {**{k: led[k] for k in ("llm_usd", "compute_usd", "total_usd", "calls", "prompt_tokens", "completion_tokens", "compute_seconds")},
                    "backend": learner.state.get("backend")},
        "wall_time_s": round(time.time() - learner.started, 1),
        "practice_episodes": sum(r["n"] for r in learner.rounds),
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "skill_file": "best_skill.py",
    }


def card_markdown(card: dict) -> str:
    ev = card.get("eval") or {}
    lines = [
        f"# Skill card: {card['title']}",
        "",
        f"**Task:** {card['instruction']}",
        "",
        f"- Demonstrations used: **0**",
        f"- Reward during practice: `{card['reward']}`" + (" (custom instruction, vision judge only)" if card.get("custom_instruction") else ""),
        f"- Perception and physics: `{card.get('realism', 'sim')}`" + (" (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)" if card.get("realism") == "real" else " (about 2 mm noise, light randomisation)"),
        f"- Practice: {len(card['rounds'])} rounds, {card['practice_episodes']} episodes; best version from round {card.get('best_round')}",
    ]
    if ev:
        lines.append(f"- Held-out success ({'ground truth' if ev.get('source') == 'gt' else 'vision judge'}): "
                     f"**{ev['k']}/{ev['n']} = {_pct(ev['p'])}** (Wilson 95% CI {_pct(ev['lo'])} to {_pct(ev['hi'])})")
        lines.append(f"- Safety layer: {ev.get('halts', 0)} halts, {ev.get('safety_clamps', 0)} clamps over {ev['n']} episodes")
        j = ev.get("judge")
        if j and j.get("decided"):
            lines.append(f"- Vision judge vs ground truth ({j['n']} episodes): accuracy {_pct(j['accuracy'])}, "
                         f"abstained {_pct(j['abstain_rate'])}, false-success rate {_pct(j['false_success_rate'])}")
    r = card["receipt"]
    lines += ["", "## Receipt", "", "| role | model | calls | tokens in | tokens out | USD |", "|---|---|---|---|---|---|"]
    for role, m in card["models"].items():
        lines.append(f"| {role} | `{m['id']}` | {m['calls']} | {m['prompt_tokens']:,} | {m['completion_tokens']:,} | ${m['usd']:.4f} |")
    lines.append(f"| compute | {r.get('backend')} | | | {r.get('compute_seconds', 0):.0f} s | ${r['compute_usd']:.4f} |")
    lines.append(f"| **total** | | {r['calls']} | {r['prompt_tokens']:,} | {r['completion_tokens']:,} | **${r['total_usd']:.4f}** |")
    if card.get("mock"):
        lines += ["", "> MOCK RUN: the coder replayed canned code. Token counts are estimates. This tests plumbing, not learning."]
    lines += ["", "## Rounds", "", "| round | success | errors | cumulative USD |", "|---|---|---|---|"]
    for rd in card["rounds"]:
        lines.append(f"| {rd['round']} | {rd['k']}/{rd['n']} | {rd['errors']} | ${rd['usd_cum']:.4f} |")
    if ev.get("failures"):
        lines += ["", "## Failure gallery (held-out)", ""]
        for f in ev["failures"]:
            lines.append(f"- seed {f['seed']}: {f.get('error') or ''} {json.dumps(f.get('metrics') or {})}")
    return "\n".join(lines) + "\n"


def card_html(card: dict, run_dir: Path) -> str:
    ev = card.get("eval") or {}
    esc = html.escape
    rows = "".join(
        f"<tr><td>{esc(role)}</td><td><code>{esc(m['id'])}</code></td><td>{m['calls']}</td><td>{m['prompt_tokens']:,}</td>"
        f"<td>{m['completion_tokens']:,}</td><td>${m['usd']:.4f}</td></tr>" for role, m in card["models"].items())
    r = card["receipt"]
    bars = "".join(
        f"<div class='bar'><span style='height:{max(2, int(rd['success'] * 100))}%'></span><em>R{rd['round']}<br>{rd['k']}/{rd['n']}</em></div>"
        for rd in card["rounds"])
    gallery = "".join(
        f"<figure>{'<img src=' + chr(34) + esc(f['frame']) + chr(34) + '>' if f.get('frame') else ''}<figcaption>seed {f['seed']}<br>{esc(f.get('error') or '')}</figcaption></figure>"
        for f in ev.get("failures", []))
    ci = ""
    if ev:
        ci = (f"<div class='ci'><div class='ci-band' style='left:{ev['lo'] * 100:.1f}%;width:{(ev['hi'] - ev['lo']) * 100:.1f}%'></div>"
              f"<div class='ci-dot' style='left:{ev['p'] * 100:.1f}%'></div></div>")
    code = (run_dir / "best_skill.py").read_text(encoding="utf-8") if (run_dir / "best_skill.py").exists() else ""
    j = (ev.get("judge") or {})
    judge_line = (f"<p>Vision judge vs ground truth on {j['n']} held-out episodes: accuracy {_pct(j['accuracy'])}, "
                  f"abstained {_pct(j['abstain_rate'])}, false-success rate {_pct(j['false_success_rate'])}.</p>") if j.get("decided") else ""
    mock = "<p class='warn'>MOCK RUN: canned code, estimated tokens. Plumbing test only.</p>" if card.get("mock") else ""
    chips = "".join(
        f"<span class='chip'><b>{esc(role.upper())}</b>{esc(m['id'])} <em>${m.get('price_in', 0):.2f} / ${m.get('price_out', 0):.2f} per M</em></span>"
        for role, m in card["models"].items())
    history = ""
    for rd in card["rounds"]:
        k = rd["round"]
        diff_p = run_dir / f"round_{k}" / "diff.patch"
        sum_p = run_dir / f"round_{k}" / "summary.md"
        notes_p = run_dir / f"round_{k}" / "notes.md"
        diff = diff_p.read_text(encoding="utf-8") if diff_p.exists() else ""
        summ = sum_p.read_text(encoding="utf-8") if sum_p.exists() else (rd.get("summary") or "")
        notes = notes_p.read_text(encoding="utf-8") if notes_p.exists() else ""
        diff_html = "\n".join(
            f"<span class='{('add' if ln.startswith('+') and not ln.startswith('+++') else 'del' if ln.startswith('-') and not ln.startswith('---') else 'hunk' if ln.startswith('@@') else '')}'>{esc(ln)}</span>"
            for ln in diff.splitlines())
        best = " &middot; <b class='k'>best</b>" if card.get("best_round") == k else ""
        history += (f"<details{' open' if k == card.get('best_round') else ''}><summary>Round {k}: {rd['k']}/{rd['n']} practice episodes "
                    f"&middot; {rd['errors']} errors &middot; ${rd['usd_cum']:.4f} so far{best}</summary>"
                    + (f"<div class='muted'>coder notes</div><pre>{esc(notes)}</pre>" if notes.strip() else "")
                    + (f"<div class='muted'>failure analysis (summariser)</div><pre>{esc(summ)}</pre>" if summ.strip() else "")
                    + (f"<div class='muted'>code change that went into this round</div><pre class='diff'>{diff_html}</pre>" if diff.strip() else "")
                    + "</details>")
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Knack skill card: {esc(card['title'])}</title>
<style>
body{{font:14px/1.45 ui-sans-serif,'Segoe UI',Roboto,sans-serif;background:#0b0e12;color:#d9dee5;margin:0;padding:32px}}
.wrap{{max-width:980px;margin:auto}} h1{{font:600 26px ui-monospace,Consolas,monospace;letter-spacing:.04em;color:#fff;margin:0 0 4px}}
.k{{color:#c6ff3d}} .muted{{color:#7d8794}} code,pre{{font:12px ui-monospace,Consolas,monospace}}
.big{{font:700 54px ui-monospace,Consolas,monospace;color:#c6ff3d}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
section{{border:1px solid #232a33;padding:16px;margin:16px 0;background:#0f1318}}
table{{border-collapse:collapse;width:100%}} td,th{{border-bottom:1px solid #232a33;padding:6px 8px;text-align:left}}
.ci{{position:relative;height:14px;background:#151a21;border:1px solid #232a33;margin:10px 0}}
.ci-band{{position:absolute;top:0;bottom:0;background:#3a4a12}} .ci-dot{{position:absolute;top:-3px;width:3px;height:20px;background:#c6ff3d}}
.bars{{display:flex;gap:10px;align-items:flex-end;height:140px}} .bar{{width:46px;height:100%;display:flex;flex-direction:column;justify-content:flex-end;text-align:center}}
.bar span{{display:block;background:#c6ff3d}} .bar em{{font:11px ui-monospace,monospace;color:#7d8794;font-style:normal;margin-top:4px}}
figure{{display:inline-block;margin:0 8px 8px 0;width:220px}} figure img{{width:220px;border:1px solid #ff5d3d}} figcaption{{font-size:11px;color:#7d8794}}
pre{{background:#07090c;padding:12px;overflow:auto;max-height:420px;border:1px solid #232a33;white-space:pre-wrap}} .warn{{color:#ffb020}}
.chip{{display:inline-block;border:1px solid #2e3742;padding:3px 8px;margin:0 6px 6px 0;font:11px ui-monospace,Consolas,monospace}}
.chip b{{background:#c6ff3d;color:#0b0e12;padding:0 4px;margin-right:6px}} .chip em{{color:#7d8794;font-style:normal;margin-left:6px}}
details{{border-top:1px solid #232a33;padding:8px 0}} summary{{cursor:pointer;font:12px ui-monospace,Consolas,monospace}}
.diff .add{{color:#c6ff3d}} .diff .del{{color:#ff5d3d}} .diff .hunk{{color:#8a94a3}}
</style></head><body><div class="wrap">
<h1><span class="k">KNACK</span> / skill card</h1>
<div class="muted">{esc(card['run_id'])} &middot; {esc(card['created'])}</div>
{mock}
<section><div class="muted">TASK</div><h2 style="margin:4px 0 0">{esc(card['instruction'])}</h2>
<p class="muted">0 demonstrations &middot; reward: {esc(card['reward'])} &middot; perception: {esc(card.get('realism', 'sim'))} &middot; {card['practice_episodes']} practice episodes in {len(card['rounds'])} rounds</p>
<div>{chips}</div></section>
<div class="grid"><section><div class="muted">HELD-OUT SUCCESS ({esc(ev.get('source', 'n/a'))})</div>
<div class="big">{_pct(ev.get('p'))}</div><div>{ev.get('k', '-')}/{ev.get('n', '-')} layouts &middot; Wilson 95% CI {_pct(ev.get('lo'))} to {_pct(ev.get('hi'))}</div>{ci}
<p class="muted">Safety layer: {ev.get('halts', 0)} halts, {ev.get('safety_clamps', 0)} clamps.</p>{judge_line}</section>
<section><div class="muted">PRACTICE CURVE</div><div class="bars">{bars}</div></section></div>
<section><div class="muted">RECEIPT</div><table><tr><th>role</th><th>model</th><th>calls</th><th>tokens in</th><th>tokens out</th><th>USD</th></tr>{rows}
<tr><td>compute</td><td>{esc(str(r.get('backend')))}</td><td></td><td></td><td>{r.get('compute_seconds', 0):.0f} s</td><td>${r['compute_usd']:.4f}</td></tr>
<tr><th>total</th><th></th><th>{r['calls']}</th><th>{r['prompt_tokens']:,}</th><th>{r['completion_tokens']:,}</th><th>${r['total_usd']:.4f}</th></tr></table></section>
<section><div class="muted">HOW IT GOT THERE</div>{history or '<p class="muted">No rounds.</p>'}</section>
<section><div class="muted">FAILURE GALLERY</div>{gallery or '<p class="muted">No held-out failures.</p>'}</section>
<section><div class="muted">SKILL (best_skill.py)</div><pre>{esc(code)}</pre></section>
</div></body></html>"""


def write_card(learner) -> dict:
    card = build_card(learner)
    d = learner.dir
    (d / "card.json").write_text(json.dumps(card, indent=1, default=str), encoding="utf-8")
    (d / "card.md").write_text(card_markdown(card), encoding="utf-8")
    (d / "card.html").write_text(card_html(card, d), encoding="utf-8")
    return card


def rebuild(run_dir) -> dict:
    """Re-render card.md/html from an existing card.json."""
    d = Path(run_dir)
    card = json.loads((d / "card.json").read_text(encoding="utf-8"))
    (d / "card.md").write_text(card_markdown(card), encoding="utf-8")
    (d / "card.html").write_text(card_html(card, d), encoding="utf-8")
    return card
