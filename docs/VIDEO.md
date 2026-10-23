# 3-minute video script

Rules this must satisfy: public YouTube, at most 3:00, at least 1 minute of the key app modules
in action (no hardware) or of hardware operating, and Nebius Token Factory + the NVIDIA models
named out loud, not just on screen. Lead with the problem, show the aha in the first 30 seconds.

Record at 1920x1080. Console: `knack ui`, browser zoom 90%, dark theme as shipped.
Every number spoken must be on screen from a real run file.

| Time | Picture | Voice-over (about 150 words per minute) |
|---|---|---|
| 0:00-0:12 | Grid GIF: 16 arms stacking cubes at once (`knack replay runs/<best> --n 16`). Title "Knack". | "These sixteen robots learned to stack cubes. Nobody showed them how. No demonstrations, no hand-written code." |
| 0:12-0:30 | Text cards: "50 to 200 demos" / "days of hand-tuning". Then the console empty state. | "Teaching a cheap robot arm a new task today costs days of engineering or hundreds of teleoperated demos. Knack lets the robot practise instead, in simulation, with NVIDIA Nemotron writing and fixing its code." |
| 0:30-1:30 | **Live console, one take.** Type the task, press PRACTISE. Loop rail lights WRITE (Nemotron 3 Ultra chip), tiles go amber, then green and red. Click a red tile: error text. Loop moves to ANALYSE (Lightning chip), failure analysis appears with line numbers. REWRITE, diff tab shows the fix. Round 2 tiles turn mostly green. | "I type the task. Nemotron 3 Ultra, served by Nebius Token Factory, writes version one. Eight arms try it on random layouts. Red means failed. Nemotron 3.5 Lightning reads the traces and finds the cause: here, line [[n]], the gripper closes above the cube. Ultra rewrites the code; this is the diff. Round two: [[k]] of eight." (speed up the waits 4x, say so on screen) |
| 1:30-1:55 | Skill card: held-out %, CI bar, receipt per model, round history. | "When practice ends, the skill is tested on a hundred layouts it never saw: [[k]] percent, with a 95 percent interval. Total cost: [[usd]] dollars. Every token is on the receipt, by model." |
| 1:55-2:20 | Vision judge: tiles with "VL pass 0.92" and an UNSURE tile. Chart: judge accuracy vs abstention. | "Real robots have no ground truth. So Nemotron 3.5 Super VL judges success from camera frames, and abstains when it is not sure. Against ground truth it was right [[x]] percent of the time and abstained on [[y]] percent." |
| 2:20-2:40 | Scoreboard chart: Nano, Super, Ultra, DeepSeek; ASPIRE points as hollow markers. | "Which Nemotron do you need? [[finding]]. NVIDIA's own ASPIRE cost chart has no Nemotron on it. This is the first point." |
| 2:40-2:52 | Architecture slide: loop with model chips; safety layer box under the skill; Nebius Serverless Jobs box. | "The learned skill is plain Python inside a fixed safety layer. No model in the control loop, so it runs on a cheap arm with no cloud." |
| 2:52-3:00 | Limitations slide (3 bullets) + repo URL. | "Simulation only so far, simplified arm, judge can be wrong. It's all in the repo. Knack." |

## Shot checklist

- [ ] The 0:30-1:30 segment is one continuous real run (counts toward the 1 minute of modules in action).
- [ ] "Nebius Token Factory" said at least twice; each NVIDIA model named when its chip lights up.
- [ ] No API key visible anywhere (terminal history, .env, browser tabs).
- [ ] Any sped-up footage is labelled "4x".
- [ ] Final numbers match `card.json` / `scoreboard_summary.json` exactly.
- [ ] If a real SO-101 run exists, replace 2:40-2:52 with it and drop the architecture slide to a 3-second inset.
