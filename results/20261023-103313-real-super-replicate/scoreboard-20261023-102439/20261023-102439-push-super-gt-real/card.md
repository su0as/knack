# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 6
- Held-out success (ground truth): **32/50 = 64%** (Wilson 95% CI 50% to 76%)
- Safety layer: 1 halts, 3 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 8 | 31,364 | 11,824 | $0.0201 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 28,505 | 1,736 | $0.0021 |
| compute | local | | | 219 s | $0.0000 |
| **total** | | 13 | 59,869 | 13,560 | **$0.0222** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 4/8 | 0 | $0.0025 |
| 2 | 0/8 | 0 | $0.0074 |
| 3 | 2/8 | 0 | $0.0109 |
| 4 | 0/8 | 0 | $0.0160 |
| 5 | 2/8 | 0 | $0.0192 |
| 6 | 6/8 | 0 | $0.0222 |

## Failure gallery (held-out)

- seed 100000:  {"puck_to_target_xy": 0.0386, "tolerance": 0.035, "upright": true}
- seed 100003:  {"puck_to_target_xy": 0.0442, "tolerance": 0.035, "upright": true}
- seed 100004:  {"puck_to_target_xy": 0.038, "tolerance": 0.035, "upright": true}
- seed 100011: SafetyViolation: target x=0.015 m is outside the safe workspace [0.04, 0.32] by 0.025 m [skill.py line 40, in run: robot.move_to(approach_x, approach_y, safe_z,] {"puck_to_target_xy": 0.0382, "tolerance": 0.035, "upright": true}
- seed 100015:  {"puck_to_target_xy": 0.038, "tolerance": 0.035, "upright": true}
- seed 100020:  {"puck_to_target_xy": 0.0427, "tolerance": 0.035, "upright": true}
- seed 100021:  {"puck_to_target_xy": 0.0492, "tolerance": 0.035, "upright": true}
- seed 100024:  {"puck_to_target_xy": 0.039, "tolerance": 0.035, "upright": true}
