## TL;DR
Type one sentence. **NVIDIA Nemotron on Nebius Token Factory** writes a Python program for a robot arm, eight simulated arms practise it on random layouts, **Nemotron 3.5 Lightning** explains every failure line by line, the coder rewrites, and Knack measures the result on **50 layouts it never practised on**, with a 95% confidence interval and a dollar receipt. Zero demonstrations.

- **Hero run:** round 1 **0/8** (every lift ended 4.91 to 4.95 cm against a 5 cm target), round 2 **8/8**, held-out **50/50**, **$0.0082** of Token Factory calls.
- **Fresh live run in the video:** 0/8, 0/8, 0/8, 1/8, 5/8, then a regression to 0/8. Knack **rolled back** to round 5, re-checked it 16/16 on fresh layouts, and scored **48/50 held-out** (95% CI 87% to 99%) for **$0.025** in 4 minutes.

## Problem and audience
Teaching a robot arm a new tabletop task costs days of hand-written code or 50 to 200 teleoperated demonstrations. Robotics students, small labs, classrooms and makers with a low-cost arm (SO-101 class) have neither, and no way to know how reliable a skill is before trusting it. Knack gives them a working skill, a measured success rate and a receipt.

## Which model does what (all on Nebius Token Factory)
| Role | Model | Why |
|---|---|---|
| Coder: writes and rewrites `skill.py` | `nvidia/nemotron-3-super-120b-a12b` (or `nvidia/Nemotron-3-Ultra-550b-a55b`) | strong open coder; Super at a third of Ultra's price was enough for most skills |
| Trace summariser | `nvidia/Nemotron-3_5-Lightning` (thinking off) | reads token-heavy traces so the coder reads a short, line-cited analysis; about 4 s per call |
| Optional vision judge | `nvidia/Nemotron-3.5-Super-VL` | reward without simulator ground truth, which a real robot needs; measured, not trusted (below) |
| Small-model test | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | can a 3B-active model program a robot? sometimes: lift 0% to 88% after practice |

Token Factory accelerated the whole loop: an OpenAI-compatible endpoint (we only swapped `base_url`), per-request `chat_template_kwargs.enable_thinking` (10x fewer tokens for the summariser), detailed `usage` for exact per-role receipts, and per-token prices low enough that a full learning run costs cents, so every experiment could be repeated.

## How it works
1. **Write:** the coder sees the task sentence, a small robot API (observe, get_pose, move_to, grasp, release) and one example observation. Nothing else.
2. **Practise:** 8 MuJoCo episodes in parallel on randomised layouts (positions, yaw, mass, friction, grip). Perception can be simulator state, camera-grade noise, or **OpenCV 5 on rendered RGB-D cameras**.
3. **Score:** ground truth, or the Nemotron VL judge on camera frames (abstains when unsure).
4. **Analyse:** Lightning groups failures into modes and cites code lines.
5. **Rewrite, keep the best:** the coder patches; if a round gets worse Knack reverts; the top versions are re-checked on 16 fresh layouts so a lucky 8-episode score cannot win.
6. **Verify:** 50 unseen layouts, Wilson 95% interval, skill card with every round's diff and a cost receipt.

The skill is plain Python with **no model in the control loop**, inside a deterministic safety layer (workspace box, joint and speed limits, table-force limit) that AI-written code cannot override.

## Results (every number is a file in the repo, `results` branch)
- **Practice pays off when perception is noisy.** Camera-grade noise: Nemotron 3 Super push **6% to 82%** (repeat run 24% to 64%), Super lift **0% to 84%**, Nano lift **0% to 88%**, all on 50 held-out layouts, for cents.
- **Scoreboard:** with standard perception Nemotron 3 Ultra solved all six scenes at 90 to 100% held-out for $0.004 to $0.065 per skill. With OpenCV perception Super scored 42/50, 48/50, 50/50, 49/50 on lift, push, stack, sort for $0.038 in total.
- **Don't trust a judge you haven't measured.** Nemotron 3.5 Super VL agreed with ground truth on 52/52 stack episodes, and a skill trained only on its verdicts scored 49/50. On lift it approved 28/28 lifts that ended a millimetre short, and the skill trained on it scored **0/50**. A vision reward works when the criterion is visible and gets gamed when it is not.
- **Honest failures:** Ultra only 56% on push with OpenCV perception; Nano never learns push or sort; Kimi K3 failed twice on push (request timeouts and one HTTP 529 "System is overloaded").

## Challenges
Our first gripper flicked cubes away (the hand-written reference fixtures caught it before any model was blamed). Live runs exposed three problems a mock never could: Lightning with thinking on returned half a thought as its answer; Ultra regressed itself from 88% to 0% by editing its own broken rewrite (now reverts); and 8-episode practice scores picked a "best" round that was no better on held-out (now re-checks on 16 fresh layouts).

## Limitations
Simulation only: no physical arm has run a learned skill yet. The Serverless Jobs backend is written but never ran because AI Cloud billing needed a $25 card top-up (details in the feedback). The sandbox is a guardrail, not a security boundary.

## What's next
Run a learned skill on a real SO-101 (`knack/real/` backend is written), desk photo to simulated twin, and practice at scale on Nebius Serverless Jobs.

Built solo by Suhas Suren (MSc Robotics, NTU Singapore). Code: https://github.com/su0as/knack (MIT).
