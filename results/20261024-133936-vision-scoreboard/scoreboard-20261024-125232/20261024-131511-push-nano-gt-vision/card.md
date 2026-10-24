# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 3
- Held-out success (ground truth): **0/50 = 0%** (Wilson 95% CI 0% to 7%)
- Safety layer: 21 halts, 21 clamps over 50 episodes
- OpenCV perception on held-out episodes: 184/185 object sightings (99%), median per-episode position error 0.32 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 7 | 28,584 | 26,187 | $0.0080 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 28,443 | 2,145 | $0.0022 |
| compute | local | | | 225 s | $0.0000 |
| **total** | | 12 | 57,027 | 28,332 | **$0.0102** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0014 |
| 2 | 0/8 | 3 | $0.0032 |
| 3 | 0/8 | 3 | $0.0046 |
| 4 | 0/8 | 1 | $0.0062 |
| 5 | 0/8 | 1 | $0.0081 |
| 6 | 0/8 | 3 | $0.0102 |

## Failure gallery (held-out)

- seed 100000:  {"puck_to_target_xy": 0.1099, "tolerance": 0.035, "upright": true}
- seed 100001: SafetyViolation: target x=0.003 m is outside the safe workspace [0.04, 0.32] by 0.037 m [skill.py line 82, in run: robot.move_by(dx=ux * push_distance,] {"puck_to_target_xy": 0.0958, "tolerance": 0.035, "upright": true}
- seed 100002:  {"puck_to_target_xy": 0.1143, "tolerance": 0.035, "upright": true}
- seed 100003: SafetyViolation: target x=-0.024 m is outside the safe workspace [0.04, 0.32] by 0.064 m [skill.py line 82, in run: robot.move_by(dx=ux * push_distance,] {"puck_to_target_xy": 0.1042, "tolerance": 0.035, "upright": true}
- seed 100004:  {"puck_to_target_xy": 0.107, "tolerance": 0.035, "upright": true}
- seed 100005: SafetyViolation: target y=-0.281 m is outside the safe workspace [-0.26, 0.26] by 0.021 m [skill.py line 82, in run: robot.move_by(dx=ux * push_distance,] {"puck_to_target_xy": 0.1067, "tolerance": 0.035, "upright": true}
- seed 100006:  {"puck_to_target_xy": 0.0993, "tolerance": 0.035, "upright": true}
- seed 100007:  {"puck_to_target_xy": 0.1009, "tolerance": 0.035, "upright": true}
