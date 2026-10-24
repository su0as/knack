# Skill card: Stack

**Task:** Stack the red cube on top of the blue cube and let go.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **49/50 = 98%** (Wilson 95% CI 90% to 100%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `moonshotai/Kimi-K3` | 1 | 1,610 | 7,988 | $0.1203 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 92 s | $0.0000 |
| **total** | | 1 | 1,610 | 7,988 | **$0.1203** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.1203 |

## Failure gallery (held-out)

- seed 100034:  {"xy_offset": 0.0617, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
