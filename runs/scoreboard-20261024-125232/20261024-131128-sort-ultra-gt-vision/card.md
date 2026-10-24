# Skill card: Sort by colour

**Task:** Put the red cube into the red tray and the blue cube into the blue tray.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **49/50 = 98%** (Wilson 95% CI 90% to 100%)
- Safety layer: 0 halts, 0 clamps over 50 episodes
- OpenCV perception on held-out episodes: 499/502 object sightings (99%), median per-episode position error 0.03 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/Nemotron-3-Ultra-550b-a55b` | 1 | 1,818 | 1,604 | $0.0066 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 136 s | $0.0000 |
| **total** | | 1 | 1,818 | 1,604 | **$0.0066** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0066 |

## Failure gallery (held-out)

- seed 100015:  {"red_cube_tray_dx": 0.0037, "red_cube_tray_dy": 0.0039, "red_cube_z": 0.0189, "red_cube_held": false, "blue_cube_tray_dx": 0.0274, "blue_cube_tray_dy": 0.2414, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": true, "blue_ok": "False"}
