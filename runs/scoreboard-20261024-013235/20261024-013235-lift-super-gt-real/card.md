# Skill card: Lift

**Task:** Pick up the red cube and hold it at least 5 cm above the table.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 4 rounds, 32 episodes; best version from round 4
- Held-out success (ground truth): **42/50 = 84%** (Wilson 95% CI 71% to 92%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 5 | 16,919 | 8,466 | $0.0127 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 3 | 11,877 | 1,115 | $0.0010 |
| compute | local | | | 168 s | $0.0000 |
| **total** | | 8 | 28,796 | 9,581 | **$0.0137** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 1/8 | 0 | $0.0033 |
| 2 | 5/8 | 1 | $0.0067 |
| 3 | 7/8 | 0 | $0.0101 |
| 4 | 8/8 | 0 | $0.0137 |

## Failure gallery (held-out)

- seed 100000:  {"red_cube_z": 0.0644, "required_z": 0.065}
- seed 100020:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100021:  {"red_cube_z": 0.0629, "required_z": 0.065}
- seed 100025:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100028:  {"red_cube_z": 0.0649, "required_z": 0.065}
- seed 100035:  {"red_cube_z": 0.0639, "required_z": 0.065}
- seed 100039:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100041:  {"red_cube_z": 0.0149, "required_z": 0.065}
