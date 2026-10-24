# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 4
- Held-out success (ground truth): **8/50 = 16%** (Wilson 95% CI 8% to 29%)
- Safety layer: 0 halts, 0 clamps over 50 episodes
- OpenCV perception on held-out episodes: 373/373 object sightings (100%), median per-episode position error 0.34 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/Nemotron-3-Ultra-550b-a55b` | 6 | 29,723 | 32,178 | $0.1263 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 34,757 | 2,009 | $0.0026 |
| compute | local | | | 353 s | $0.0000 |
| **total** | | 11 | 64,480 | 34,187 | **$0.1288** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0071 |
| 2 | 0/8 | 0 | $0.0214 |
| 3 | 0/8 | 2 | $0.0693 |
| 4 | 3/8 | 2 | $0.0803 |
| 5 | 0/8 | 0 | $0.0926 |
| 6 | 0/8 | 3 | $0.1288 |

## Failure gallery (held-out)

- seed 100000:  {"puck_to_target_xy": 0.0813, "tolerance": 0.035, "upright": true}
- seed 100001:  {"puck_to_target_xy": 0.0821, "tolerance": 0.035, "upright": true}
- seed 100002: AttributeError: 'SimRobot' object has no attribute 'MotionError' [skill.py line 82, in run: except robot.MotionError:] {"puck_to_target_xy": 0.1978, "tolerance": 0.035, "upright": true}
- seed 100003:  {"puck_to_target_xy": 0.0817, "tolerance": 0.035, "upright": true}
- seed 100004:  {"puck_to_target_xy": 0.2006, "tolerance": 0.035, "upright": true}
- seed 100005:  {"puck_to_target_xy": 0.0837, "tolerance": 0.035, "upright": true}
- seed 100007:  {"puck_to_target_xy": 0.0826, "tolerance": 0.035, "upright": true}
- seed 100008:  {"puck_to_target_xy": 0.1013, "tolerance": 0.035, "upright": true}
