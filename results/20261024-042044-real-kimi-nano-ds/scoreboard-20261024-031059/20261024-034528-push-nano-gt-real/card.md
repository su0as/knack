# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 1
- Held-out success (ground truth): **0/50 = 0%** (Wilson 95% CI 0% to 7%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 6 | 28,729 | 25,155 | $0.0078 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 42,298 | 1,997 | $0.0030 |
| compute | local | | | 304 s | $0.0000 |
| **total** | | 11 | 71,027 | 27,152 | **$0.0108** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0008 |
| 2 | 0/8 | 1 | $0.0025 |
| 3 | 0/8 | 0 | $0.0036 |
| 4 | 0/8 | 0 | $0.0052 |
| 5 | 0/8 | 0 | $0.0079 |
| 6 | 0/8 | 0 | $0.0108 |

## Failure gallery (held-out)

- seed 100000:  {"puck_to_target_xy": 0.1135, "tolerance": 0.035, "upright": true}
- seed 100001:  {"puck_to_target_xy": 0.1021, "tolerance": 0.035, "upright": true}
- seed 100002:  {"puck_to_target_xy": 0.1134, "tolerance": 0.035, "upright": true}
- seed 100003:  {"puck_to_target_xy": 0.1161, "tolerance": 0.035, "upright": true}
- seed 100004:  {"puck_to_target_xy": 0.1108, "tolerance": 0.035, "upright": true}
- seed 100005:  {"puck_to_target_xy": 0.115, "tolerance": 0.035, "upright": true}
- seed 100006:  {"puck_to_target_xy": 0.0985, "tolerance": 0.035, "upright": true}
- seed 100007:  {"puck_to_target_xy": 0.1137, "tolerance": 0.035, "upright": true}
