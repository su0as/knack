# Skill card: Lift

**Task:** Pick up the red cube and hold it at least 5 cm above the table.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 4 rounds, 32 episodes; best version from round 4
- Held-out success (ground truth): **42/50 = 84%** (Wilson 95% CI 71% to 92%)
- Safety layer: 0 halts, 9 clamps over 50 episodes
- OpenCV perception on held-out episodes: 586/604 object sightings (97%), median per-episode position error 4.19 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 6 | 19,670 | 11,783 | $0.0165 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 3 | 12,969 | 996 | $0.0010 |
| compute | local | | | 332 s | $0.0000 |
| **total** | | 9 | 32,639 | 12,779 | **$0.0175** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 8 | $0.0034 |
| 2 | 0/8 | 0 | $0.0070 |
| 3 | 4/8 | 0 | $0.0110 |
| 4 | 8/8 | 0 | $0.0175 |

## Failure gallery (held-out)

- seed 100007:  {"red_cube_z": 0.0632, "required_z": 0.065}
- seed 100010:  {"red_cube_z": 0.0637, "required_z": 0.065}
- seed 100030:  {"red_cube_z": 0.064, "required_z": 0.065}
- seed 100036:  {"red_cube_z": 0.0649, "required_z": 0.065}
- seed 100043:  {"red_cube_z": 0.064, "required_z": 0.065}
- seed 100045:  {"red_cube_z": 0.0639, "required_z": 0.065}
- seed 100046:  {"red_cube_z": 0.0644, "required_z": 0.065}
- seed 100049:  {"red_cube_z": 0.0648, "required_z": 0.065}
