# Skill card: Stack

**Task:** Stack the red cube on top of the blue cube and let go.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Practice: 4 rounds, 32 episodes; best version from round 2
- Held-out success (ground truth): **36/50 = 72%** (Wilson 95% CI 58% to 83%)
- Safety layer: 0 halts, 48 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 4 | 18,484 | 23,273 | $0.0265 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 3 | 16,797 | 1,293 | $0.0013 |
| compute | local | | | 146 s | $0.0000 |
| **total** | | 7 | 35,281 | 24,566 | **$0.0278** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 5/8 | 0 | $0.0020 |
| 2 | 6/8 | 0 | $0.0113 |
| 3 | 0/8 | 0 | $0.0187 |
| 4 | 5/8 | 0 | $0.0278 |

## Failure gallery (held-out)

- seed 100001:  {"xy_offset": 0.1776, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100002:  {"xy_offset": 0.1246, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100006:  {"xy_offset": 0.1001, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
- seed 100008:  {"xy_offset": 0.118, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100016:  {"xy_offset": 0.1209, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
- seed 100018:  {"xy_offset": 0.0975, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
- seed 100019:  {"xy_offset": 0.1756, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100025:  {"xy_offset": 0.1322, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
