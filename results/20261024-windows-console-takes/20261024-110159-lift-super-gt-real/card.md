# Skill card: Lift

**Task:** Pick up the red cube and hold it at least 5 cm above the table.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 2
- Held-out success (ground truth): **20/50 = 40%** (Wilson 95% CI 28% to 54%)
- Safety layer: 0 halts, 3 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 8 | 28,925 | 14,208 | $0.0215 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 21,398 | 2,157 | $0.0018 |
| compute | local | | | 286 s | $0.0000 |
| **total** | | 13 | 50,323 | 16,365 | **$0.0233** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0014 |
| 2 | 5/8 | 0 | $0.0055 |
| 3 | 1/8 | 0 | $0.0093 |
| 4 | 0/8 | 0 | $0.0140 |
| 5 | 0/8 | 0 | $0.0194 |
| 6 | 3/8 | 0 | $0.0233 |

## Failure gallery (held-out)

- seed 100001:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100002:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100003:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100004:  {"red_cube_z": 0.0614, "required_z": 0.065}
- seed 100006:  {"red_cube_z": 0.0558, "required_z": 0.065}
- seed 100007:  {"red_cube_z": 0.0639, "required_z": 0.065}
- seed 100008:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100009:  {"red_cube_z": 0.0149, "required_z": 0.065}
