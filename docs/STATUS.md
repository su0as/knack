# Status and test checklist

Last updated: 23 Oct 2026, 10:30 SGT.

## State

- Code complete for the core loop, console, skill card, experiments, MCP server, Serverless Jobs runner and SO-101 backend.
- CI green on Linux and Windows. Reference fixtures (hand-written test skills, never shown to the model) solve all 6 scenes on 20/20 layouts each.
- Offline mock run of the full pipeline passes in CI (canned coder, no tokens).
- Token Factory key created and stored only in `D:\dev\knack\.env` (gitignored). Model IDs verified with the free `/models` call. **No paid model call has been made yet.**
- Not yet run: any live Nemotron call, the pilot gate, the Serverless Jobs backend (paid), the real arm.

## Your test checklist (in order, cheapest first)

1. `powershell -ExecutionPolicy Bypass -File D:\dev\knack\bootstrap.ps1`
   Links the folder to GitHub, makes `.venv`, installs, then runs the three free checks below. Sign in to GitHub if git asks (private repo).
2. `knack check`: MuJoCo, rendering, key present.
3. `knack oracle --n 10`: every scene should be 10/10. If not, send me the output.
4. `knack learn lift --mock` then `knack ui`: the console shows a finished mock run (loop rail, tiles, card).
5. `knack models --remote`: lists the 5 NVIDIA models (free).
6. **First paid call (decide first: account is on the $1 trial; promo code not applied yet):** `knack learn lift --coder super --budget 0.30`.
7. `knack pilot` (gate: Super and Ultra on lift/place/push, $0.90 cap). Pass = held-out >= 50% on 2 of 3 tasks for at least one model.
8. Only then: `knack exp scoreboard`, `knack exp ablation`, `knack exp judge runs/`, `knack exp plots ...`, and `knack nebius hello` (AI Cloud, paid, not covered by credits).

Each session afterwards: `. D:\dev\knack\scripts\env_windows.ps1`

## Decisions pending (yours)

- Apply the Token Factory promo code `NEBIUS-DEVPOST-GLOBAL26` (Billing page) before step 6, or keep to the $1 trial.
- SO-101 purchase (after the pilot result).
- Making the repo public (it is private now). Before that: `git log -p | Select-String NEBIUS_API_KEY=v1` must return nothing.

## Docs to fill after real runs

- `docs/DEVPOST.md`: every `[[...]]` placeholder.
- `docs/VIDEO.md`: numbers in the voice-over.
- `docs/FEEDBACK.md`: the TODO items (first-call latency, rate limits, judge behaviour).
- README Results section.
