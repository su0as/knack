# Skill card: Lift

**Task:** Pick up the red cube and hold it at least 5 cm above the table.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 4
- Held-out success (ground truth): **44/50 = 88%** (Wilson 95% CI 76% to 94%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 6 | 28,138 | 28,879 | $0.0086 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 30,827 | 1,844 | $0.0023 |
| compute | local | | | 289 s | $0.0000 |
| **total** | | 11 | 58,965 | 30,723 | **$0.0109** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0005 |
| 2 | 0/8 | 0 | $0.0021 |
| 3 | 0/8 | 0 | $0.0039 |
| 4 | 7/8 | 0 | $0.0054 |
| 5 | 5/8 | 0 | $0.0091 |
| 6 | 3/8 | 0 | $0.0109 |

## Failure gallery (held-out)

- seed 100016:  {"red_cube_z": 0.0166, "required_z": 0.065}
- seed 100017:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100036:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100037:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100039:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100041:  {"red_cube_z": 0.0148, "required_z": 0.065}
