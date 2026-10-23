# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Practice: 4 rounds, 32 episodes; best version from round 1
- Held-out success (ground truth): **45/50 = 90%** (Wilson 95% CI 79% to 96%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/Nemotron-3-Ultra-550b-a55b` | 4 | 13,058 | 16,927 | $0.0638 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 3 | 9,929 | 1,031 | $0.0008 |
| compute | local | | | 137 s | $0.0000 |
| **total** | | 7 | 22,987 | 17,958 | **$0.0647** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 7/8 | 0 | $0.0063 |
| 2 | 0/8 | 0 | $0.0280 |
| 3 | 0/8 | 0 | $0.0428 |
| 4 | 0/8 | 0 | $0.0647 |

## Failure gallery (held-out)

- seed 100004:  {"puck_to_target_xy": 0.0913, "tolerance": 0.035, "upright": true}
- seed 100016:  {"puck_to_target_xy": 0.0503, "tolerance": 0.035, "upright": true}
- seed 100026:  {"puck_to_target_xy": 0.0535, "tolerance": 0.035, "upright": true}
- seed 100032:  {"puck_to_target_xy": 0.0378, "tolerance": 0.035, "upright": true}
- seed 100041:  {"puck_to_target_xy": 0.0678, "tolerance": 0.035, "upright": true}
