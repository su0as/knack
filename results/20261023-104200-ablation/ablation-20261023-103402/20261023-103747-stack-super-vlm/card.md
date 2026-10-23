# Skill card: Stack

**Task:** Stack the red cube on top of the blue cube and let go.

- Demonstrations used: **0**
- Reward during practice: `vlm`
- Perception and physics: `sim` (about 2 mm noise, light randomisation)
- Practice: 4 rounds, 32 episodes; best version from round 4
- Held-out success (ground truth): **49/50 = 98%** (Wilson 95% CI 90% to 100%)
- Safety layer: 0 halts, 15 clamps over 50 episodes
- Vision judge vs ground truth (20 episodes): accuracy 100%, abstained 0%, false-success rate n/a

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 5 | 18,149 | 12,574 | $0.0164 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 3 | 14,005 | 1,041 | $0.0011 |
| judge | `nvidia/Nemotron-3.5-Super-VL` | 52 | 67,080 | 22,257 | $0.0402 |
| compute | local | | | 99 s | $0.0000 |
| **total** | | 60 | 99,234 | 35,872 | **$0.0576** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 7/8 | 0 | $0.0079 |
| 2 | 7/8 | 0 | $0.0212 |
| 3 | 0/8 | 0 | $0.0307 |
| 4 | 7/8 | 0 | $0.0428 |

## Failure gallery (held-out)

- seed 100027:  {"xy_offset": 0.0515, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
