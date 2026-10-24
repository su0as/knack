# Skill card: Sort by colour

**Task:** Put the red cube into the red tray and the blue cube into the blue tray.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 1
- Held-out success (ground truth): **0/50 = 0%** (Wilson 95% CI 0% to 7%)
- Safety layer: 1 halts, 75 clamps over 50 episodes
- OpenCV perception on held-out episodes: 100/100 object sightings (100%), median per-episode position error 0.03 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 6 | 28,924 | 23,973 | $0.0075 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 31,377 | 2,024 | $0.0024 |
| compute | local | | | 240 s | $0.0000 |
| **total** | | 11 | 60,301 | 25,997 | **$0.0099** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0009 |
| 2 | 0/8 | 0 | $0.0024 |
| 3 | 0/8 | 0 | $0.0043 |
| 4 | 0/8 | 0 | $0.0059 |
| 5 | 0/8 | 0 | $0.0077 |
| 6 | 0/8 | 0 | $0.0099 |

## Failure gallery (held-out)

- seed 100000:  {"red_cube_tray_dx": 0.1121, "red_cube_tray_dy": 0.2061, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0478, "blue_cube_tray_dy": 0.2512, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100001:  {"red_cube_tray_dx": 0.0011, "red_cube_tray_dy": 0.0697, "red_cube_z": 0.015, "red_cube_held": false, "blue_cube_tray_dx": 0.0842, "blue_cube_tray_dy": 0.1576, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100002:  {"red_cube_tray_dx": 0.0496, "red_cube_tray_dy": 0.0932, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.1183, "blue_cube_tray_dy": 0.0773, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100003:  {"red_cube_tray_dx": 0.0787, "red_cube_tray_dy": 0.0069, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.006, "blue_cube_tray_dy": 0.2763, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100004:  {"red_cube_tray_dx": 0.0769, "red_cube_tray_dy": 0.055, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.053, "blue_cube_tray_dy": 0.2255, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100005:  {"red_cube_tray_dx": 0.0315, "red_cube_tray_dy": 0.1827, "red_cube_z": 0.0158, "red_cube_held": false, "blue_cube_tray_dx": 0.1305, "blue_cube_tray_dy": 0.1263, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100006:  {"red_cube_tray_dx": 0.0692, "red_cube_tray_dy": 0.0228, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0366, "blue_cube_tray_dy": 0.3388, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100007:  {"red_cube_tray_dx": 0.026, "red_cube_tray_dy": 0.0791, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0283, "blue_cube_tray_dy": 0.082, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
