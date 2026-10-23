# Skill card: Stack

**Task:** Stack the red cube on top of the blue cube and let go.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 2
- Held-out success (ground truth): **32/50 = 64%** (Wilson 95% CI 50% to 76%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/Nemotron-3-Ultra-550b-a55b` | 6 | 28,116 | 26,002 | $0.1061 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 21,222 | 1,963 | $0.0017 |
| compute | local | | | 119 s | $0.0000 |
| **total** | | 11 | 49,338 | 27,965 | **$0.1079** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 4/8 | 0 | $0.0051 |
| 2 | 7/8 | 0 | $0.0300 |
| 3 | 5/8 | 0 | $0.0618 |
| 4 | 5/8 | 0 | $0.0844 |
| 5 | 5/8 | 0 | $0.0958 |
| 6 | 4/8 | 0 | $0.1079 |

## Failure gallery (held-out)

- seed 100002:  {"xy_offset": 0.0914, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100003:  {"xy_offset": 0.1304, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100008:  {"xy_offset": 0.0362, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
- seed 100009:  {"xy_offset": 0.0379, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100011:  {"xy_offset": 0.0363, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
- seed 100012:  {"xy_offset": 0.0162, "z_gap": 0.0296, "red_held": false, "blue_z": 0.0148}
- seed 100013:  {"xy_offset": 0.04, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100017:  {"xy_offset": 0.037, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
