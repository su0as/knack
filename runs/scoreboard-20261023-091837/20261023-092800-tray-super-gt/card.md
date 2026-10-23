# Skill card: Into the tray

**Task:** Put the yellow cube into the tray and let go of it.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Practice: 4 rounds, 32 episodes; best version from round 4
- Held-out success (ground truth): **32/50 = 64%** (Wilson 95% CI 50% to 76%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 4 | 15,433 | 7,944 | $0.0118 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 3 | 12,496 | 1,159 | $0.0010 |
| compute | local | | | 139 s | $0.0000 |
| **total** | | 7 | 27,929 | 9,103 | **$0.0128** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 4/8 | 0 | $0.0017 |
| 2 | 3/8 | 0 | $0.0053 |
| 3 | 5/8 | 0 | $0.0086 |
| 4 | 6/8 | 0 | $0.0128 |

## Failure gallery (held-out)

- seed 100001:  {"yellow_cube_tray_dx": 0.0169, "yellow_cube_tray_dy": 0.1666, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
- seed 100002:  {"yellow_cube_tray_dx": 0.0151, "yellow_cube_tray_dy": 0.0766, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
- seed 100003:  {"yellow_cube_tray_dx": 0.0423, "yellow_cube_tray_dy": 0.0698, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
- seed 100006:  {"yellow_cube_tray_dx": 0.0024, "yellow_cube_tray_dy": 0.0756, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
- seed 100008:  {"yellow_cube_tray_dx": 0.038, "yellow_cube_tray_dy": 0.0942, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
- seed 100012:  {"yellow_cube_tray_dx": 0.0353, "yellow_cube_tray_dy": 0.0656, "yellow_cube_z": 0.0207, "yellow_cube_held": false}
- seed 100016:  {"yellow_cube_tray_dx": 0.0136, "yellow_cube_tray_dy": 0.1599, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
- seed 100018:  {"yellow_cube_tray_dx": 0.0126, "yellow_cube_tray_dy": 0.1044, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
