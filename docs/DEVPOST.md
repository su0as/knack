# Devpost submission draft: Knack

Draft for nebiusglobalaihackathon.devpost.com, Physical AI track. Every `[[...]]` is a placeholder
that must be filled from a file in `runs/` before submitting. Do not round up, do not estimate.

---

## Tagline (max ~200 chars)

Type a task. Simulated robots practise it in parallel, NVIDIA Nemotron rewrites the robot's code after every failure, and you get a verified skill with a receipt. Zero demonstrations.

## Inspiration

Teaching a cheap robot arm a new tabletop task costs either days of hand-tuned code or 50 to 200 teleoperated demonstrations. Two releases this month showed a third route: NVIDIA GEAR's ASPIRE (coding agents that discover robot skills) and Yilun Du's RAX (scale exploration, not demonstrations). ASPIRE published a success-vs-API-cost chart for 12 coding models. Nemotron is not on it. We wanted to know whether NVIDIA's own open models, served per token on Nebius, can do this job, and what a working skill costs.

## What it does

1. You pick a scene and type a task, for example "Stack the red cube on top of the blue cube and let go."
2. **Nemotron 3 Ultra** writes a Python skill against a small robot API (observe, get_pose, move_to, grasp, release).
3. Eight simulated arms practise that skill in parallel on randomised layouts (positions, yaw, mass, friction, grip force).
4. Each episode is scored by the simulator's ground truth, or by **Nemotron 3.5 Super VL** looking at camera frames, which abstains when unsure.
5. **Nemotron 3.5 Lightning** reads the long execution traces and groups the failures into modes, citing code lines.
6. Ultra rewrites the skill. Repeat until the target or the round limit.
7. The best version is evaluated on 100 unseen layouts and you get a **skill card**: held-out success with a Wilson 95% interval, the code diff of every round, a failure gallery and a dollar receipt per model.

The learned skill is plain Python. It runs locally with no model in the control loop, inside a deterministic safety layer (workspace box, joint and speed limits, elbow clearance, table-force limit) that the AI-written code cannot catch or override.

## Which model does what

| Role | Model (Nebius Token Factory) | Why |
|---|---|---|
| Coder | `nvidia/Nemotron-3-Ultra-550b-a55b` | strongest open reasoning model for code |
| Cheaper coder | `nvidia/nemotron-3-super-120b-a12b` | is a model at 30% of the price enough? |
| Trace summariser | `nvidia/Nemotron-3_5-Lightning` | reads token-heavy traces so the expensive coder reads a short analysis |
| Vision judge | `nvidia/Nemotron-3.5-Super-VL` | reward that works without simulator ground truth, which is what a real robot needs |
| Baseline | `deepseek-ai/DeepSeek-V4.1-Flash` | the model RAX used, as an outside reference |

## Results (fill from runs/, never from memory)

- Pilot gate (Super and Ultra on lift, place, push; 4 rounds): [[pilot.md: PASS/FAIL, per-task held-out %]]
- Model scoreboard: [[scoreboard_summary.json: mean held-out success and $/skill for nano, super, ultra, deepseek-flash]]
- Reward source ablation (ground truth vs vision judge vs self-report): [[ablation_summary.json]]. Self-report is included on purpose: it shows how an agent that grades itself declares success it did not achieve.
- Vision judge vs ground truth on [[n]] stored episodes: accuracy [[x]], abstention [[y]], false-success rate [[z]] at threshold 0.6. [[judge_eval.json]]
- Cheapest verified skill: [[task]], [[k/100]] held-out, $[[usd]] total.
- ASPIRE's open-weight points for context (different benchmark, LIBERO-Pro): Kimi K3 about 78% at about $55 per task, Qwen 3.8 Max about 56% at about $40 per task.

## How we built it

- **Simulator:** MuJoCo, scenes generated in Python (no mesh downloads), a 5-DoF arm with SO-101 proportions, analytic IK shared with the real-arm backend. Six scenes: lift, place, push (a puck too wide to grasp), stack, tray, sort.
- **Practice runner:** one OS process per episode with a wall-clock kill; the same worker runs inside a Nebius AI Cloud Serverless Job for larger batches (`--backend nebius`, CPU preset, stock python image, results to Object Storage).
- **Agent loop:** `knack/agent.py`. Coder notes carry facts across rounds. Best round chosen on practice score, final number only from held-out layouts.
- **Ledger:** every Token Factory call is logged with tokens, cost and role, so the card's receipt is exact.
- **Console:** a small local web app: loop rail showing which model is working, live grid of practising robots, per-round diffs, skill card.
- **MCP server:** the same robot tools over MCP, so any agent can drive the arm.
- **CI:** Linux and Windows. A hand-written reference skill must solve every scene on 20 layouts (they are test fixtures, never shown to the model; a test checks no prompt contains them), plus an offline mock run of the whole pipeline.

## Challenges

- Our first gripper flicked cubes away; the fixtures exposed it (85% on lift, 50% on push) before any model was blamed.
- Keeping "zero demonstrations" honest: the coder sees the task text, the API doc and one example observation. Nothing else.
- [[what broke in the live runs]]

## What we learned

- [[from runs]]

## Limitations

Published in `docs/LIMITATIONS.md`: simplified arm, easy perception in sim, guardrail sandbox rather than a security boundary, real-arm and Serverless Jobs paths [[tested / untested]], vision judge can be wrong (measured, not assumed).

## What's next

- Run a learned skill on a real SO-101 (backend written, `knack/real/`).
- Desk photo to simulated twin, so practice starts from your own table.
- Put Nemotron on ASPIRE's own benchmark (LIBERO-Pro subset).

## Built with

Nebius Token Factory, Nebius AI Cloud (Serverless Jobs), NVIDIA Nemotron 3 Ultra, Nemotron 3 Super, Nemotron 3 Nano, Nemotron 3.5 Lightning, Nemotron 3.5 Super VL, MuJoCo, Python, OpenAI Python SDK, MCP.

## Links

- Code (MIT): https://github.com/su0as/knack
- Video: [[YouTube URL, public]]
- Feedback on Nebius and NVIDIA tools: `docs/FEEDBACK.md`
