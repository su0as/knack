# Skill card: Stack

**Task:** Stack the red cube on top of the blue cube and let go.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 2 rounds, 16 episodes; best version from round 2
- Held-out success (ground truth): **48/50 = 96%** (Wilson 95% CI 87% to 99%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `deepseek-ai/DeepSeek-V4.1-Flash` | 3 | 13,202 | 31,595 | $0.0399 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 1 | 5,468 | 374 | $0.0004 |
| compute | local | | | 161 s | $0.0000 |
| **total** | | 4 | 18,670 | 31,969 | **$0.0403** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 6/8 | 0 | $0.0097 |
| 2 | 8/8 | 0 | $0.0403 |

## Failure gallery (held-out)

- seed 100012:  {"xy_offset": 0.0336, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
- seed 100041:  {"xy_offset": 0.0362, "z_gap": -0.0, "red_held": false, "blue_z": 0.0149}
