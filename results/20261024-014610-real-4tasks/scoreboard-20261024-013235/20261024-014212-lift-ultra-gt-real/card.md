# Skill card: Lift

**Task:** Pick up the red cube and hold it at least 5 cm above the table.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **44/50 = 88%** (Wilson 95% CI 76% to 94%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/Nemotron-3-Ultra-550b-a55b` | 1 | 1,606 | 946 | $0.0044 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 76 s | $0.0000 |
| **total** | | 1 | 1,606 | 946 | **$0.0044** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0044 |

## Failure gallery (held-out)

- seed 100002:  {"red_cube_z": 0.0148, "required_z": 0.065}
- seed 100003:  {"red_cube_z": 0.015, "required_z": 0.065}
- seed 100013:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100017:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100028:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100037:  {"red_cube_z": 0.0149, "required_z": 0.065}
