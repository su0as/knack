# Skill card: Place in circle

**Task:** Put the blue cube inside the green circle on the table and let go of it.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **40/50 = 80%** (Wilson 95% CI 67% to 89%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 1 | 1,670 | 1,489 | $0.0018 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 92 s | $0.0000 |
| **total** | | 1 | 1,670 | 1,489 | **$0.0018** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0018 |

## Failure gallery (held-out)

- seed 100003:  {"blue_cube_to_target_xy": 0.1029, "tolerance": 0.03, "blue_cube_z": 0.0149, "held": false}
- seed 100011:  {"blue_cube_to_target_xy": 0.1091, "tolerance": 0.03, "blue_cube_z": 0.0117, "held": false}
- seed 100013:  {"blue_cube_to_target_xy": 0.0893, "tolerance": 0.03, "blue_cube_z": 0.0202, "held": false}
- seed 100017:  {"blue_cube_to_target_xy": 0.1308, "tolerance": 0.03, "blue_cube_z": 0.0149, "held": false}
- seed 100018:  {"blue_cube_to_target_xy": 0.0912, "tolerance": 0.03, "blue_cube_z": 0.0198, "held": false}
- seed 100020:  {"blue_cube_to_target_xy": 0.0827, "tolerance": 0.03, "blue_cube_z": 0.0135, "held": false}
- seed 100021:  {"blue_cube_to_target_xy": 0.0321, "tolerance": 0.03, "blue_cube_z": 0.0149, "held": false}
- seed 100025:  {"blue_cube_to_target_xy": 0.1133, "tolerance": 0.03, "blue_cube_z": 0.0204, "held": false}
