# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 6
- Held-out success (ground truth): **41/50 = 82%** (Wilson 95% CI 69% to 90%)
- Safety layer: 0 halts, 2 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 9 | 31,513 | 17,849 | $0.0255 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 29,332 | 1,690 | $0.0022 |
| compute | local | | | 130 s | $0.0000 |
| **total** | | 14 | 60,845 | 19,539 | **$0.0277** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0031 |
| 2 | 1/8 | 0 | $0.0064 |
| 3 | 1/8 | 0 | $0.0099 |
| 4 | 1/8 | 0 | $0.0189 |
| 5 | 0/8 | 0 | $0.0241 |
| 6 | 4/8 | 0 | $0.0277 |

## Failure gallery (held-out)

- seed 100004:  {"puck_to_target_xy": 0.1056, "tolerance": 0.035, "upright": true}
- seed 100005:  {"puck_to_target_xy": 0.1115, "tolerance": 0.035, "upright": true}
- seed 100007:  {"puck_to_target_xy": 0.1135, "tolerance": 0.035, "upright": true}
- seed 100016:  {"puck_to_target_xy": 0.1055, "tolerance": 0.035, "upright": true}
- seed 100030:  {"puck_to_target_xy": 0.0826, "tolerance": 0.035, "upright": true}
- seed 100032:  {"puck_to_target_xy": 0.0981, "tolerance": 0.035, "upright": true}
- seed 100036:  {"puck_to_target_xy": 0.0441, "tolerance": 0.035, "upright": true}
- seed 100045:  {"puck_to_target_xy": 0.1188, "tolerance": 0.035, "upright": true}
