# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 6
- Held-out success (ground truth): **5/50 = 10%** (Wilson 95% CI 4% to 21%)
- Safety layer: 16 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/Nemotron-3-Ultra-550b-a55b` | 6 | 32,979 | 21,231 | $0.0967 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 45,980 | 1,794 | $0.0032 |
| compute | local | | | 277 s | $0.0000 |
| **total** | | 11 | 78,959 | 23,025 | **$0.0999** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 1 | $0.0056 |
| 2 | 1/8 | 5 | $0.0179 |
| 3 | 0/8 | 8 | $0.0488 |
| 4 | 0/8 | 8 | $0.0617 |
| 5 | 1/8 | 6 | $0.0769 |
| 6 | 1/8 | 0 | $0.0999 |

## Failure gallery (held-out)

- seed 100001: EpisodeTimeout: time budget of 45 s exceeded [skill.py line 128, in run: robot.move_by(dx=push_distance * push_dir[0],] {"puck_to_target_xy": 0.1027, "tolerance": 0.035, "upright": true}
- seed 100002:  {"puck_to_target_xy": 0.07, "tolerance": 0.035, "upright": true}
- seed 100004: EpisodeTimeout: time budget of 45 s exceeded [skill.py line 128, in run: robot.move_by(dx=push_distance * push_dir[0],] {"puck_to_target_xy": 0.0761, "tolerance": 0.035, "upright": true}
- seed 100005: EpisodeTimeout: time budget of 45 s exceeded [skill.py line 128, in run: robot.move_by(dx=push_distance * push_dir[0],] {"puck_to_target_xy": 0.0897, "tolerance": 0.035, "upright": true}
- seed 100006:  {"puck_to_target_xy": 0.0401, "tolerance": 0.035, "upright": true}
- seed 100007: EpisodeTimeout: time budget of 45 s exceeded [skill.py line 121, in run: robot.move_to(start_xy[0], start_xy[1], local_push_z, speed=0.05, yaw=push_yaw)] {"puck_to_target_xy": 0.1136, "tolerance": 0.035, "upright": true}
- seed 100008:  {"puck_to_target_xy": 0.0377, "tolerance": 0.035, "upright": true}
- seed 100009: EpisodeTimeout: time budget of 45 s exceeded [skill.py line 128, in run: robot.move_by(dx=push_distance * push_dir[0],] {"puck_to_target_xy": 0.0781, "tolerance": 0.035, "upright": true}
