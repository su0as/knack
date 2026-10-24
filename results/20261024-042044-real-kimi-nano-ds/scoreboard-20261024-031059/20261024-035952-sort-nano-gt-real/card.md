# Skill card: Sort by colour

**Task:** Put the red cube into the red tray and the blue cube into the blue tray.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 4
- Held-out success (ground truth): **21/50 = 42%** (Wilson 95% CI 29% to 56%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 7 | 37,628 | 24,605 | $0.0082 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 39,002 | 1,977 | $0.0028 |
| compute | local | | | 307 s | $0.0000 |
| **total** | | 12 | 76,630 | 26,582 | **$0.0110** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 1 | $0.0009 |
| 2 | 0/8 | 0 | $0.0026 |
| 3 | 3/8 | 0 | $0.0051 |
| 4 | 4/8 | 0 | $0.0069 |
| 5 | 2/8 | 0 | $0.0088 |
| 6 | 5/8 | 0 | $0.0110 |

## Failure gallery (held-out)

- seed 100003:  {"red_cube_tray_dx": 0.0757, "red_cube_tray_dy": 0.0872, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.006, "blue_cube_tray_dy": 0.2763, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100004:  {"red_cube_tray_dx": 0.0557, "red_cube_tray_dy": 0.1038, "red_cube_z": 0.0137, "red_cube_held": false, "blue_cube_tray_dx": 0.0595, "blue_cube_tray_dy": 0.2685, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100005:  {"red_cube_tray_dx": 0.0006, "red_cube_tray_dy": 0.0185, "red_cube_z": 0.025, "red_cube_held": false, "blue_cube_tray_dx": 0.0952, "blue_cube_tray_dy": 0.1369, "blue_cube_z": 0.0181, "blue_cube_held": false, "red_ok": true, "blue_ok": "False"}
- seed 100006:  {"red_cube_tray_dx": 0.0152, "red_cube_tray_dy": 0.0035, "red_cube_z": 0.0189, "red_cube_held": false, "blue_cube_tray_dx": 0.0042, "blue_cube_tray_dy": 0.2016, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": true, "blue_ok": "False"}
- seed 100008:  {"red_cube_tray_dx": 0.0203, "red_cube_tray_dy": 0.0243, "red_cube_z": 0.022, "red_cube_held": false, "blue_cube_tray_dx": 0.0413, "blue_cube_tray_dy": 0.3035, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": true, "blue_ok": "False"}
- seed 100009:  {"red_cube_tray_dx": 0.006, "red_cube_tray_dy": 0.0278, "red_cube_z": 0.0189, "red_cube_held": false, "blue_cube_tray_dx": 0.0975, "blue_cube_tray_dy": 0.2609, "blue_cube_z": 0.0148, "blue_cube_held": false, "red_ok": true, "blue_ok": "False"}
- seed 100010:  {"red_cube_tray_dx": 0.0248, "red_cube_tray_dy": 0.1218, "red_cube_z": 0.0205, "red_cube_held": false, "blue_cube_tray_dx": 0.0458, "blue_cube_tray_dy": 0.2839, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100011:  {"red_cube_tray_dx": 0.0102, "red_cube_tray_dy": 0.0234, "red_cube_z": 0.0283, "red_cube_held": false, "blue_cube_tray_dx": 0.0703, "blue_cube_tray_dy": 0.3057, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": true, "blue_ok": "False"}
