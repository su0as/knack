# Status and test checklist

Last updated: 23 Oct 2026, 18:30 SGT.

## State

- Code complete for the core loop, console, skill card, experiments, MCP server, Serverless Jobs runner and SO-101 backend.
- CI green on Linux and Windows. Reference fixtures (hand-written test skills, never shown to the model) solve all 6 scenes on 20/20 layouts each.
- Offline mock run of the full pipeline passes in CI (canned coder, no tokens).
- Token Factory keys: one on the Windows laptop (`D:\dev\knack\.env`, gitignored) and one stored only as the GitHub Actions secret `NEBIUS_API_KEY` (key name "knack-github-actions (Aside)").
- **Live runs now go through `.github/workflows/live.yml`** (Actions tab, "Run workflow", or `gh workflow run live.yml -f command="..."`). Each run uploads `runs/` as an artifact and commits the small summary files to the `results` branch. One paid run at a time (concurrency group), every command still has `--budget`.
- **Pilot gate: PASS** (23 Oct): Super 100/100/80% and Ultra 100/100/90% held-out on lift/place/push. Scoreboard on stack/tray/sort done. Camera-grade (`--realism real`) runs done for stack and push. See README Results.
- Spent so far: about $0.50 of the $1 trial. Promo code form submitted (code arrives by email to suhas.cse20@gmail.com, $25); AI Builder Program application submitted (another $25 after review, "within two business days").
- Done since: reward ablation and judge accuracy, camera-grade scoreboard for Nano / Super / Ultra / DeepSeek / Kimi K3, practice-gain re-runs, README charts, Windows console fixes (realism dropdown, WinError 5 retries, stale runs).
- Token Factory balance: $59 from two promo codes (24 Oct), minus about $1.50 of runs.
- **Serverless Jobs: code and CI wiring ready, not run.** Nebius AI Cloud account created (tenant amber-tiglon-tenant-h35, project default-project-eu-west2). Blocked on billing: the console requires card details and charges a $25 top-up before the first job. After that: create a service account (editors group) + authorized key, an Object Storage bucket + access key, then set repo secrets NEBIUS_SA_ID, NEBIUS_SA_PUBLIC_KEY_ID, NEBIUS_SA_PRIVATE_KEY, NEBIUS_PROJECT_ID, NEBIUS_S3_ACCESS_KEY_ID, NEBIUS_S3_SECRET_ACCESS_KEY, KNACK_NEBIUS_BUCKET, NEBIUS_REGION=eu-west2, then `live` with `nebius hello` and `learn lift --coder super --realism real --backend nebius`.
- Not run: the real arm.

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

- When the promo-code email arrives, redeem it in Token Factory (Billing), then the remaining experiments can run.
- SO-101 purchase (after the pilot result).
- Making the repo public (it is private now). Before that: `git log -p | Select-String NEBIUS_API_KEY=v1` must return nothing.

## Docs to fill after real runs

- `docs/DEVPOST.md`: every `[[...]]` placeholder.
- `docs/VIDEO.md`: numbers in the voice-over.
- `docs/FEEDBACK.md`: the TODO items (first-call latency, rate limits, judge behaviour).
- README Results section.
