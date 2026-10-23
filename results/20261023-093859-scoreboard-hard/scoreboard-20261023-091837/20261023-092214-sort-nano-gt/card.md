# Skill card: Sort by colour

**Task:** Put the red cube into the red tray and the blue cube into the blue tray.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Practice: 4 rounds, 32 episodes; best version from round 4
- Held-out success (ground truth): **0/50 = 0%** (Wilson 95% CI 0% to 7%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 4 | 16,746 | 16,246 | $0.0049 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 3 | 15,469 | 978 | $0.0012 |
| compute | local | | | 117 s | $0.0000 |
| **total** | | 7 | 32,215 | 17,224 | **$0.0061** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0007 |
| 2 | 0/8 | 0 | $0.0027 |
| 3 | 0/8 | 0 | $0.0043 |
| 4 | 0/8 | 0 | $0.0061 |

## Failure gallery (held-out)

- seed 100000:  {"red_cube_tray_dx": 0.0117, "red_cube_tray_dy": 0.1424, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0374, "blue_cube_tray_dy": 0.2492, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100001:  {"red_cube_tray_dx": 0.0271, "red_cube_tray_dy": 0.1517, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0747, "blue_cube_tray_dy": 0.1669, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100002:  {"red_cube_tray_dx": 0.0859, "red_cube_tray_dy": 0.1075, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.1167, "blue_cube_tray_dy": 0.081, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100003:  {"red_cube_tray_dx": 0.0747, "red_cube_tray_dy": 0.0936, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.006, "blue_cube_tray_dy": 0.2763, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100004:  {"red_cube_tray_dx": 0.053, "red_cube_tray_dy": 0.1013, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0595, "blue_cube_tray_dy": 0.2685, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100005:  {"red_cube_tray_dx": 0.0131, "red_cube_tray_dy": 0.1095, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0837, "blue_cube_tray_dy": 0.1449, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100006:  {"red_cube_tray_dx": 0.091, "red_cube_tray_dy": 0.0709, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0111, "blue_cube_tray_dy": 0.2786, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100007:  {"red_cube_tray_dx": 0.099, "red_cube_tray_dy": 0.0856, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0151, "blue_cube_tray_dy": 0.1093, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
