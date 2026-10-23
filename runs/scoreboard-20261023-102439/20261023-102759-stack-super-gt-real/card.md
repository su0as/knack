# Skill card: Stack

**Task:** Stack the red cube on top of the blue cube and let go.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 5
- Held-out success (ground truth): **31/50 = 62%** (Wilson 95% CI 48% to 74%)
- Safety layer: 0 halts, 33 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 10 | 43,632 | 30,571 | $0.0406 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 30,464 | 1,908 | $0.0023 |
| compute | local | | | 253 s | $0.0000 |
| **total** | | 15 | 74,096 | 32,479 | **$0.0429** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 5/8 | 0 | $0.0029 |
| 2 | 3/8 | 1 | $0.0111 |
| 3 | 5/8 | 0 | $0.0199 |
| 4 | 6/8 | 0 | $0.0275 |
| 5 | 6/8 | 0 | $0.0344 |
| 6 | 3/8 | 0 | $0.0429 |

## Failure gallery (held-out)

- seed 100001:  {"xy_offset": 0.0166, "z_gap": 0.0295, "red_held": false, "blue_z": 0.0148}
- seed 100009:  {"xy_offset": 0.0217, "z_gap": 0.0287, "red_held": false, "blue_z": 0.0148}
- seed 100011:  {"xy_offset": 0.0251, "z_gap": 0.0263, "red_held": false, "blue_z": 0.0148}
- seed 100012:  {"xy_offset": 0.0176, "z_gap": 0.0295, "red_held": false, "blue_z": 0.0148}
- seed 100014:  {"xy_offset": 0.0213, "z_gap": 0.0283, "red_held": false, "blue_z": 0.0147}
- seed 100016:  {"xy_offset": 0.0335, "z_gap": 0.0014, "red_held": false, "blue_z": 0.0139}
- seed 100017:  {"xy_offset": 0.0219, "z_gap": 0.0281, "red_held": false, "blue_z": 0.0148}
- seed 100021:  {"xy_offset": 0.0239, "z_gap": 0.0277, "red_held": false, "blue_z": 0.0148}
