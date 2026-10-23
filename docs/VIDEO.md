# 3-minute video script

Rules this must satisfy: public YouTube, at most 3:00, at least 1 minute of the key app modules
in action (no hardware) or of hardware operating, and Nebius Token Factory + the NVIDIA models
named out loud, not just on screen. Lead with the problem, show the aha in the first 30 seconds.

Record at 1920x1080. Console: `knack ui`, browser zoom 90%, dark theme as shipped.
Every number spoken must be on screen from a real run file.

| Time | Picture | Voice-over (about 150 words per minute) |
|---|---|---|
| 0:00-0:12 | `docs/media/first_try_vs_practised_push.gif` full screen (full-size version: `knack replay <run> --compare`). Title "Knack". | "Top row: the first program an AI wrote for this robot. Zero for six. Bottom row: the same AI after practising on its own mistakes. No demonstrations, no hand-written code." |
| 0:12-0:30 | Text cards: "50 to 200 demos" / "days of hand-tuning". Then the console empty state. | "Teaching a cheap robot arm a new task today costs days of engineering or hundreds of teleoperated demos. Knack lets the robot practise instead, in simulation, with NVIDIA Nemotron writing and fixing its code." |
| 0:30-1:30 | **Live console, one take.** Type the task, press PRACTISE. Loop rail lights WRITE (Nemotron 3 Ultra chip), tiles go amber, then green and red. Click a red tile: error text. Loop moves to ANALYSE (Lightning chip), failure analysis appears with line numbers. REWRITE, diff tab shows the fix. Round 2 tiles turn mostly green. | "I type the task. Nemotron 3 Ultra, served by Nebius Token Factory, writes version one. Eight arms try it on random layouts. Red means failed. Nemotron 3.5 Lightning reads the traces and finds the cause, with the line number. The coder rewrites the code; this is the diff. Next round: more green." (speed up the waits 4x, say so on screen) |
| 1:30-1:55 | Skill card of the push run: 82% held-out, CI bar, receipt per model, round history. | "Then the skill is tested on fifty layouts it never saw. The first version managed six percent. After practice, eighty-two. Total cost: under three cents. Every token is on the receipt, by model." |
| 1:55-2:20 | Ablation table: stack 49/50 with the vision judge as the only reward; lift 0/50. Two judge frames side by side. | "Real robots have no ground truth, so Nemotron 3.5 Super VL can judge success from camera frames. On stacking it agreed with ground truth every single time, and the skill it trained reached ninety-eight percent. On lifting 'at least five centimetres' it could not see the millimetres, called every short lift a success, and the skill failed. We publish both." |
| 2:20-2:40 | Scoreboard table: Ultra 90-100% on all six scenes at $0.004-$0.065 per skill; Nano, Super, DeepSeek alongside. | "Which Nemotron do you need? Ultra wrote all six skills, mostly first try, for under seven cents each. NVIDIA's own ASPIRE cost chart has no Nemotron on it. These are the first points." |
| 2:40-2:52 | Architecture slide: loop with model chips; safety layer box under the skill; Nebius Serverless Jobs box. | "The learned skill is plain Python inside a fixed safety layer. No model in the control loop, so it runs on a cheap arm with no cloud." |
| 2:52-3:00 | Limitations slide (3 bullets) + repo URL. | "Simulation only so far, simplified arm, judge can be wrong. It's all in the repo. Knack." |

## Shot checklist

- [ ] The 0:30-1:30 segment is one continuous real run (counts toward the 1 minute of modules in action).
- [ ] "Nebius Token Factory" said at least twice; each NVIDIA model named when its chip lights up.
- [ ] No API key visible anywhere (terminal history, .env, browser tabs).
- [ ] Any sped-up footage is labelled "4x".
- [ ] Final numbers match `card.json` / `scoreboard_summary.json` exactly.
- [ ] If a real SO-101 run exists, replace 2:40-2:52 with it and drop the architecture slide to a 3-second inset.
