# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **40/50 = 80%** (Wilson 95% CI 67% to 89%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 3 | 5,238 | 3,694 | $0.0049 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 97 s | $0.0000 |
| **total** | | 3 | 5,238 | 3,694 | **$0.0049** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0049 |

## Failure gallery (held-out)

- seed 100000:  {"puck_to_target_xy": 0.0367, "tolerance": 0.035, "upright": true}
- seed 100012:  {"puck_to_target_xy": 0.0356, "tolerance": 0.035, "upright": true}
- seed 100017:  {"puck_to_target_xy": 0.0357, "tolerance": 0.035, "upright": true}
- seed 100018:  {"puck_to_target_xy": 0.038, "tolerance": 0.035, "upright": true}
- seed 100019:  {"puck_to_target_xy": 0.0355, "tolerance": 0.035, "upright": true}
- seed 100030:  {"puck_to_target_xy": 0.0373, "tolerance": 0.035, "upright": true}
- seed 100033:  {"puck_to_target_xy": 0.035, "tolerance": 0.035, "upright": true}
- seed 100035:  {"puck_to_target_xy": 0.0495, "tolerance": 0.035, "upright": true}
