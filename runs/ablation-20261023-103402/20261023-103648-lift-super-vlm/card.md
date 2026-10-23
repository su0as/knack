# Skill card: Lift

**Task:** Pick up the red cube and hold it at least 5 cm above the table.

- Demonstrations used: **0**
- Reward during practice: `vlm`
- Perception and physics: `sim` (about 2 mm noise, light randomisation)
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **0/50 = 0%** (Wilson 95% CI 0% to 7%)
- Safety layer: 0 halts, 0 clamps over 50 episodes
- Vision judge vs ground truth (20 episodes): accuracy 0%, abstained 0%, false-success rate 100%

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 1 | 1,539 | 1,320 | $0.0016 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| judge | `nvidia/Nemotron-3.5-Super-VL` | 28 | 36,204 | 14,243 | $0.0237 |
| compute | local | | | 55 s | $0.0000 |
| **total** | | 29 | 37,743 | 15,563 | **$0.0253** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0086 |

## Failure gallery (held-out)

- seed 100000:  {"red_cube_z": 0.0644, "required_z": 0.065}
- seed 100001:  {"red_cube_z": 0.0643, "required_z": 0.065}
- seed 100002:  {"red_cube_z": 0.0643, "required_z": 0.065}
- seed 100003:  {"red_cube_z": 0.0644, "required_z": 0.065}
- seed 100004:  {"red_cube_z": 0.0643, "required_z": 0.065}
- seed 100005:  {"red_cube_z": 0.0643, "required_z": 0.065}
- seed 100006:  {"red_cube_z": 0.0643, "required_z": 0.065}
- seed 100007:  {"red_cube_z": 0.0643, "required_z": 0.065}
