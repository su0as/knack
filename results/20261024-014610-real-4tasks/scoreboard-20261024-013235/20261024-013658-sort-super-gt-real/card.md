# Skill card: Sort by colour

**Task:** Put the red cube into the red tray and the blue cube into the blue tray.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 5
- Held-out success (ground truth): **18/50 = 36%** (Wilson 95% CI 24% to 50%)
- Safety layer: 0 halts, 2 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 8 | 42,390 | 21,957 | $0.0325 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 53,181 | 1,990 | $0.0037 |
| compute | local | | | 361 s | $0.0000 |
| **total** | | 13 | 95,571 | 23,947 | **$0.0361** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 2/8 | 0 | $0.0062 |
| 2 | 0/8 | 0 | $0.0109 |
| 3 | 0/8 | 0 | $0.0170 |
| 4 | 0/8 | 0 | $0.0230 |
| 5 | 1/8 | 0 | $0.0290 |
| 6 | 0/8 | 0 | $0.0361 |

## Failure gallery (held-out)

- seed 100001:  {"red_cube_tray_dx": 0.0078, "red_cube_tray_dy": 0.0049, "red_cube_z": 0.0189, "red_cube_held": false, "blue_cube_tray_dx": 0.0747, "blue_cube_tray_dy": 0.1669, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": true, "blue_ok": "False"}
- seed 100003:  {"red_cube_tray_dx": 0.0747, "red_cube_tray_dy": 0.0936, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0009, "blue_cube_tray_dy": 0.013, "blue_cube_z": 0.0189, "blue_cube_held": false, "red_ok": "False", "blue_ok": true}
- seed 100005:  {"red_cube_tray_dx": 0.0154, "red_cube_tray_dy": 0.1103, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0016, "blue_cube_tray_dy": 0.0003, "blue_cube_z": 0.0189, "blue_cube_held": false, "red_ok": "False", "blue_ok": true}
- seed 100007:  {"red_cube_tray_dx": 0.1012, "red_cube_tray_dy": 0.0883, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0006, "blue_cube_tray_dy": 0.0099, "blue_cube_z": 0.0189, "blue_cube_held": false, "red_ok": "False", "blue_ok": true}
- seed 100008:  {"red_cube_tray_dx": 0.1052, "red_cube_tray_dy": 0.1022, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0271, "blue_cube_tray_dy": 0.298, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": "False", "blue_ok": "False"}
- seed 100009:  {"red_cube_tray_dx": 0.0576, "red_cube_tray_dy": 0.1405, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0101, "blue_cube_tray_dy": 0.0049, "blue_cube_z": 0.0189, "blue_cube_held": false, "red_ok": "False", "blue_ok": true}
- seed 100011:  {"red_cube_tray_dx": 0.002, "red_cube_tray_dy": 0.0078, "red_cube_z": 0.0189, "red_cube_held": false, "blue_cube_tray_dx": 0.0871, "blue_cube_tray_dy": 0.2498, "blue_cube_z": 0.0149, "blue_cube_held": false, "red_ok": true, "blue_ok": "False"}
- seed 100012:  {"red_cube_tray_dx": 0.0248, "red_cube_tray_dy": 0.2535, "red_cube_z": 0.0149, "red_cube_held": false, "blue_cube_tray_dx": 0.0016, "blue_cube_tray_dy": 0.0045, "blue_cube_z": 0.0189, "blue_cube_held": false, "red_ok": "False", "blue_ok": true}
