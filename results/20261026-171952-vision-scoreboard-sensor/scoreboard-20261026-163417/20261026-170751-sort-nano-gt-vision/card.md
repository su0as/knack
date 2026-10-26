# Skill card: Sort by colour

**Task:** Put the red cube into the red tray and the blue cube into the blue tray.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 1
- Held-out success (ground truth): **0/50 = 0%** (Wilson 95% CI 0% to 7%)
- Safety layer: 19 halts, 60 clamps over 50 episodes
- OpenCV perception on held-out episodes: 1215/1682 object sightings (72%), median per-episode position error 3.87 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 6 | 39,929 | 32,252 | $0.0101 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 51,692 | 1,931 | $0.0036 |
| compute | local | | | 1133 s | $0.0000 |
| **total** | | 11 | 91,621 | 34,183 | **$0.0137** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 4 | $0.0006 |
| 2 | 0/8 | 8 | $0.0033 |
| 3 | 0/8 | 3 | $0.0051 |
| 4 | 0/8 | 2 | $0.0073 |
| 5 | 0/8 | 3 | $0.0102 |
| 6 | 0/8 | 3 | $0.0137 |

## Failure gallery (held-out)

- seed 100000: SafetyViolation: target x=0.018 m is outside the safe workspace [0.04, 0.32] by 0.022 m [skill.py line 71, in run: resp = robot.move_to(approach_x, approach_y, target_z,] {"red_cube_tray_dx": 0.1112, "red_cube_tray_dy": 0.0501, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0937, "blue_cube_tray_dy": 0.2506, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100001:  {"red_cube_tray_dx": 0.0248, "red_cube_tray_dy": 0.1373, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.1779, "blue_cube_tray_dy": 0.0992, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100002:  {"red_cube_tray_dx": 0.0073, "red_cube_tray_dy": 0.0693, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.098, "blue_cube_tray_dy": 0.0254, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100003:  {"red_cube_tray_dx": 0.0871, "red_cube_tray_dy": 0.0821, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0194, "blue_cube_tray_dy": 0.3009, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100004:  {"red_cube_tray_dx": 0.098, "red_cube_tray_dy": 0.0287, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0315, "blue_cube_tray_dy": 0.2796, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100005:  {"red_cube_tray_dx": 0.1076, "red_cube_tray_dy": 0.121, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0731, "blue_cube_tray_dy": 0.0359, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100006:  {"red_cube_tray_dx": 0.0409, "red_cube_tray_dy": 0.1469, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0442, "blue_cube_tray_dy": 0.2964, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100007:  {"red_cube_tray_dx": 0.0831, "red_cube_tray_dy": 0.0372, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0817, "blue_cube_tray_dy": 0.0456, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
