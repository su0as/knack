# Skill card: Stack

**Task:** Stack the red cube on top of the blue cube and let go.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 5
- Held-out success (ground truth): **31/50 = 62%** (Wilson 95% CI 48% to 74%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 12 | 43,500 | 33,312 | $0.0425 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 26,232 | 1,894 | $0.0020 |
| compute | local | | | 125 s | $0.0000 |
| **total** | | 17 | 69,732 | 35,206 | **$0.0445** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 1/8 | 0 | $0.0031 |
| 2 | 6/8 | 0 | $0.0154 |
| 3 | 4/8 | 0 | $0.0193 |
| 4 | 4/8 | 0 | $0.0282 |
| 5 | 6/8 | 0 | $0.0352 |
| 6 | 4/8 | 0 | $0.0445 |

## Failure gallery (held-out)

- seed 100000:  {"xy_offset": 0.0326, "z_gap": 0.0013, "red_held": false, "blue_z": 0.0149}
- seed 100001:  {"xy_offset": 0.034, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100004:  {"xy_offset": 0.0177, "z_gap": 0.0291, "red_held": false, "blue_z": 0.0147}
- seed 100005:  {"xy_offset": 0.0347, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100006:  {"xy_offset": 0.0345, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
- seed 100009:  {"xy_offset": 0.0308, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
- seed 100015:  {"xy_offset": 0.0329, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
- seed 100017:  {"xy_offset": 0.0383, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
