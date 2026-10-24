# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 1
- Held-out success (ground truth): **36/50 = 72%** (Wilson 95% CI 58% to 83%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 8 | 33,842 | 16,944 | $0.0254 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 38,521 | 1,903 | $0.0028 |
| compute | local | | | 321 s | $0.0000 |
| **total** | | 13 | 72,363 | 18,847 | **$0.0282** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 4/8 | 0 | $0.0032 |
| 2 | 4/8 | 0 | $0.0100 |
| 3 | 0/8 | 0 | $0.0131 |
| 4 | 5/8 | 0 | $0.0177 |
| 5 | 1/8 | 0 | $0.0217 |
| 6 | 0/8 | 0 | $0.0282 |

## Failure gallery (held-out)

- seed 100000:  {"puck_to_target_xy": 0.0361, "tolerance": 0.035, "upright": true}
- seed 100003:  {"puck_to_target_xy": 0.0152, "tolerance": 0.035, "upright": false}
- seed 100011:  {"puck_to_target_xy": 0.0359, "tolerance": 0.035, "upright": true}
- seed 100015:  {"puck_to_target_xy": 0.0066, "tolerance": 0.035, "upright": false}
- seed 100016:  {"puck_to_target_xy": 0.0404, "tolerance": 0.035, "upright": true}
- seed 100022:  {"puck_to_target_xy": 0.0103, "tolerance": 0.035, "upright": true}
- seed 100025:  {"puck_to_target_xy": 0.039, "tolerance": 0.035, "upright": true}
- seed 100029:  {"puck_to_target_xy": 0.0305, "tolerance": 0.035, "upright": false}
