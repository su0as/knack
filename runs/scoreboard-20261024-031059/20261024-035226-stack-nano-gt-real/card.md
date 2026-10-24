# Skill card: Stack

**Task:** Stack the red cube on top of the blue cube and let go.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 2
- Held-out success (ground truth): **2/50 = 4%** (Wilson 95% CI 1% to 13%)
- Safety layer: 0 halts, 1 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 6 | 31,305 | 29,927 | $0.0091 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 39,870 | 1,869 | $0.0028 |
| compute | local | | | 254 s | $0.0000 |
| **total** | | 11 | 71,175 | 31,796 | **$0.0119** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0008 |
| 2 | 1/8 | 0 | $0.0022 |
| 3 | 0/8 | 0 | $0.0050 |
| 4 | 0/8 | 0 | $0.0075 |
| 5 | 0/8 | 0 | $0.0100 |
| 6 | 0/8 | 0 | $0.0119 |

## Failure gallery (held-out)

- seed 100000:  {"xy_offset": 0.022, "z_gap": 0.028, "red_held": false, "blue_z": 0.0148}
- seed 100001:  {"xy_offset": 0.1791, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100002:  {"xy_offset": 0.1378, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100003:  {"xy_offset": 0.1017, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100004:  {"xy_offset": 0.0884, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100005:  {"xy_offset": 0.0356, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
- seed 100006:  {"xy_offset": 0.1021, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100007:  {"xy_offset": 0.1775, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
