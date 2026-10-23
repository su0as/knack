# Skill card: Stack

**Task:** Stack the red cube on top of the blue cube and let go.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Practice: 4 rounds, 32 episodes; best version from round 1
- Held-out success (ground truth): **32/50 = 64%** (Wilson 95% CI 50% to 76%)
- Safety layer: 0 halts, 18 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 4 | 17,751 | 14,474 | $0.0045 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 3 | 13,320 | 1,059 | $0.0011 |
| compute | local | | | 141 s | $0.0000 |
| **total** | | 7 | 31,071 | 15,533 | **$0.0056** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 7/8 | 0 | $0.0006 |
| 2 | 4/8 | 0 | $0.0022 |
| 3 | 5/8 | 0 | $0.0040 |
| 4 | 4/8 | 0 | $0.0056 |

## Failure gallery (held-out)

- seed 100005:  {"xy_offset": 0.0447, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100008:  {"xy_offset": 0.0497, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
- seed 100010:  {"xy_offset": 0.0528, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100013:  {"xy_offset": 0.0327, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
- seed 100014:  {"xy_offset": 0.0566, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
- seed 100021:  {"xy_offset": 0.0379, "z_gap": -0.0045, "red_held": false, "blue_z": 0.0209}
- seed 100022:  {"xy_offset": 0.0555, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100023:  {"xy_offset": 0.0409, "z_gap": 0.0039, "red_held": false, "blue_z": 0.0149}
