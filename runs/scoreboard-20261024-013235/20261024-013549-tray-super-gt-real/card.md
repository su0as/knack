# Skill card: Into the tray

**Task:** Put the yellow cube into the tray and let go of it.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **44/50 = 88%** (Wilson 95% CI 76% to 94%)
- Safety layer: 1 halts, 23 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 1 | 1,684 | 1,363 | $0.0017 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 117 s | $0.0000 |
| **total** | | 1 | 1,684 | 1,363 | **$0.0017** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0017 |

## Failure gallery (held-out)

- seed 100003:  {"yellow_cube_tray_dx": 0.04, "yellow_cube_tray_dy": 0.1175, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
- seed 100008:  {"yellow_cube_tray_dx": 0.057, "yellow_cube_tray_dy": 0.1192, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
- seed 100017:  {"yellow_cube_tray_dx": 0.0387, "yellow_cube_tray_dy": 0.1451, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
- seed 100025:  {"yellow_cube_tray_dx": 0.0204, "yellow_cube_tray_dy": 0.1173, "yellow_cube_z": 0.0148, "yellow_cube_held": false}
- seed 100035: SafetyViolation: target z=-0.006 m is outside the safe workspace [0.014, 0.26] by 0.021 m [skill.py line 17, in attempt_grasp: res = robot.move_to(x, y, z, yaw=yaw, speed=0.05)] {"yellow_cube_tray_dx": 0.0043, "yellow_cube_tray_dy": 0.1117, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
- seed 100039:  {"yellow_cube_tray_dx": 0.0281, "yellow_cube_tray_dy": 0.1445, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
