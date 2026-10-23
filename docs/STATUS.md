# Status and test checklist

Last updated: 23 Oct 2026 (SGT).

## Done

- Simulator: 6 scenes, SO-101-proportioned 5-DoF arm, analytic IK, domain randomisation, 3 cameras.
- Robot API + deterministic safety layer + sandbox + per-episode process isolation.
- Practice loop: coder, trace summariser, vision judge, 3 reward sources, best-round selection, held-out eval with Wilson CI, skill card (json/md/html), skill library.
- Token Factory client with per-role cost ledger and hard USD budget; regional URL fallback.
- Experiments: pilot gate, model scoreboard, reward ablation, judge accuracy, plots.
- Console UI, GIF replay grid for videos, MCP server, Nebius Serverless Jobs runner, SO-101 backend (last two untested).
- CI on Linux (with headless rendering) and Windows; offline mock run end to end.

## Your test checklist (in order, cheapest first)

1. `knack check` : MuJoCo imports, rendering works, key is set.
2. `knack oracle --n 10` : every scene solvable (free). If a scene is below 8/10, tell me which.
3. `knack learn lift --mock` then `knack ui` : the console shows a finished mock run.
4. `knack models --remote` : confirms model IDs with your key (free).
5. `knack learn lift --coder super --budget 0.30` : first real run.
6. `knack pilot` : the gate (Super and Ultra x lift/place/push, $0.90 cap). Pass = held-out >= 50% on 2 of 3 tasks for at least one model.
7. Only then: scoreboard, ablation, judge eval, Nebius hello job (`knack nebius hello`, paid).

## Decisions pending (yours)

- SO-101 purchase (gate result first).
- Making the repo public (it is private now).
- Applying the Token Factory promo code (Billing page) before the pilot: the account shows a $1.00 trial.
