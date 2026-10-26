# Skill card: Sort by colour

**Task:** Put the red cube into the red tray and the blue cube into the blue tray.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **49/50 = 98%** (Wilson 95% CI 90% to 100%)
- Safety layer: 0 halts, 14 clamps over 50 episodes
- OpenCV perception on held-out episodes: 398/400 object sightings (100%), median per-episode position error 4.11 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 1 | 1,818 | 1,609 | $0.0020 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 194 s | $0.0000 |
| **total** | | 1 | 1,818 | 1,609 | **$0.0020** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0020 |

## Failure gallery (held-out)

- seed 100015:  {"red_cube_tray_dx": 0.0019, "red_cube_tray_dy": 0.0031, "red_cube_z": 0.0189, "red_cube_held": false, "blue_cube_tray_dx": 0.0274, "blue_cube_tray_dy": 0.2414, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": true, "blue_ok": "False"}
