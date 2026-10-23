# Skill card: Lift

**Task:** Pick up the red cube and hold it at least 5 cm above the table.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `sim` (about 2 mm noise, light randomisation)
- Practice: 4 rounds, 32 episodes; best version from round 3
- Held-out success (ground truth): **36/50 = 72%** (Wilson 95% CI 58% to 83%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 4 | 12,800 | 7,190 | $0.0103 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 3 | 8,291 | 1,040 | $0.0007 |
| compute | local | | | 139 s | $0.0000 |
| **total** | | 7 | 21,091 | 8,230 | **$0.0111** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0020 |
| 2 | 6/8 | 0 | $0.0047 |
| 3 | 7/8 | 0 | $0.0077 |
| 4 | 0/8 | 0 | $0.0111 |

## Failure gallery (held-out)

- seed 100001:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100002:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100006:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100008:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100016:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100018:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100019:  {"red_cube_z": 0.0149, "required_z": 0.065}
- seed 100025:  {"red_cube_z": 0.0149, "required_z": 0.065}
