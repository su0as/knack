# Skill card: Place in circle

**Task:** Put the blue cube inside the green circle on the table and let go of it.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **43/50 = 86%** (Wilson 95% CI 74% to 93%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/Nemotron-3-Ultra-550b-a55b` | 1 | 1,670 | 1,395 | $0.0059 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 108 s | $0.0000 |
| **total** | | 1 | 1,670 | 1,395 | **$0.0059** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0059 |

## Failure gallery (held-out)

- seed 100003:  {"blue_cube_to_target_xy": 0.0979, "tolerance": 0.03, "blue_cube_z": 0.0149, "held": false}
- seed 100017:  {"blue_cube_to_target_xy": 0.1428, "tolerance": 0.03, "blue_cube_z": 0.0149, "held": false}
- seed 100020:  {"blue_cube_to_target_xy": 0.0907, "tolerance": 0.03, "blue_cube_z": 0.0149, "held": false}
- seed 100021:  {"blue_cube_to_target_xy": 0.0329, "tolerance": 0.03, "blue_cube_z": 0.0149, "held": false}
- seed 100025:  {"blue_cube_to_target_xy": 0.0971, "tolerance": 0.03, "blue_cube_z": 0.0149, "held": false}
- seed 100028:  {"blue_cube_to_target_xy": 0.1154, "tolerance": 0.03, "blue_cube_z": 0.0149, "held": false}
- seed 100039:  {"blue_cube_to_target_xy": 0.1248, "tolerance": 0.03, "blue_cube_z": 0.0149, "held": false}
