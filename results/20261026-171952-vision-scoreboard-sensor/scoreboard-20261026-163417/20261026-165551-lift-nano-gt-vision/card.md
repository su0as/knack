# Skill card: Lift

**Task:** Pick up the red cube and hold it at least 5 cm above the table.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 1
- Held-out success (ground truth): **0/50 = 0%** (Wilson 95% CI 0% to 7%)
- Safety layer: 0 halts, 0 clamps over 50 episodes
- OpenCV perception on held-out episodes: 100/100 object sightings (100%), median per-episode position error 3.86 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 6 | 24,716 | 26,143 | $0.0078 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 22,535 | 1,882 | $0.0018 |
| compute | local | | | 278 s | $0.0000 |
| **total** | | 11 | 47,251 | 28,025 | **$0.0096** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0006 |
| 2 | 0/8 | 0 | $0.0022 |
| 3 | 0/8 | 0 | $0.0035 |
| 4 | 0/8 | 0 | $0.0064 |
| 5 | 0/8 | 0 | $0.0075 |
| 6 | 0/8 | 0 | $0.0096 |

## Failure gallery (held-out)

- seed 100000:  {"red_cube_z": 0.0495, "required_z": 0.065}
- seed 100001:  {"red_cube_z": 0.0491, "required_z": 0.065}
- seed 100002:  {"red_cube_z": 0.0493, "required_z": 0.065}
- seed 100003:  {"red_cube_z": 0.0495, "required_z": 0.065}
- seed 100004:  {"red_cube_z": 0.0492, "required_z": 0.065}
- seed 100005:  {"red_cube_z": 0.0491, "required_z": 0.065}
- seed 100006:  {"red_cube_z": 0.0492, "required_z": 0.065}
- seed 100007:  {"red_cube_z": 0.0493, "required_z": 0.065}
