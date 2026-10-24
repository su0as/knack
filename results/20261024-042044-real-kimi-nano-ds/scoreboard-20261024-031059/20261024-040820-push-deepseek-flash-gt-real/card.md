# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 4 rounds, 32 episodes; best version from round 4
- Held-out success (ground truth): **44/50 = 88%** (Wilson 95% CI 76% to 94%)
- Safety layer: 2 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `deepseek-ai/DeepSeek-V4.1-Flash` | 7 | 34,332 | 94,762 | $0.1189 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 3 | 20,063 | 1,071 | $0.0015 |
| compute | local | | | 305 s | $0.0000 |
| **total** | | 10 | 54,395 | 95,833 | **$0.1204** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 6/8 | 4 | $0.0152 |
| 2 | 5/8 | 3 | $0.0557 |
| 3 | 6/8 | 2 | $0.0963 |
| 4 | 8/8 | 0 | $0.1203 |

## Failure gallery (held-out)

- seed 100002:  {"puck_to_target_xy": 0.3003, "tolerance": 0.035, "upright": false}
- seed 100017:  {"puck_to_target_xy": 0.007, "tolerance": 0.035, "upright": false}
- seed 100023:  {"puck_to_target_xy": 0.0149, "tolerance": 0.035, "upright": false}
- seed 100026: EpisodeTimeout: time budget of 45 s exceeded [skill.py line 73, in run: robot.move_to(ex, ey, PUSH_Z, yaw=yaw, speed=0.05)] {"puck_to_target_xy": 0.0965, "tolerance": 0.035, "upright": true}
- seed 100038: EpisodeTimeout: time budget of 45 s exceeded [skill.py line 58, in run: res = robot.move_to(cx, cy, PUSH_Z, yaw=yaw, speed=0.10)] {"puck_to_target_xy": 0.1088, "tolerance": 0.035, "upright": true}
- seed 100044:  {"puck_to_target_xy": 0.0061, "tolerance": 0.035, "upright": false}
