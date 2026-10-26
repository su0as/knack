# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 1
- Held-out success (ground truth): **0/50 = 0%** (Wilson 95% CI 0% to 7%)
- Safety layer: 0 halts, 13 clamps over 50 episodes
- OpenCV perception on held-out episodes: 50/50 object sightings (100%), median per-episode position error 4.02 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 6 | 24,483 | 19,067 | $0.0060 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 21,789 | 1,599 | $0.0017 |
| compute | local | | | 301 s | $0.0000 |
| **total** | | 11 | 46,272 | 20,666 | **$0.0077** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0008 |
| 2 | 0/8 | 0 | $0.0021 |
| 3 | 0/8 | 0 | $0.0037 |
| 4 | 0/8 | 0 | $0.0051 |
| 5 | 0/8 | 0 | $0.0063 |
| 6 | 0/8 | 0 | $0.0077 |

## Failure gallery (held-out)

- seed 100000:  {"puck_to_target_xy": 0.1138, "tolerance": 0.035, "upright": true}
- seed 100001:  {"puck_to_target_xy": 0.1005, "tolerance": 0.035, "upright": true}
- seed 100002:  {"puck_to_target_xy": 0.1188, "tolerance": 0.035, "upright": true}
- seed 100003:  {"puck_to_target_xy": 0.1129, "tolerance": 0.035, "upright": true}
- seed 100004:  {"puck_to_target_xy": 0.114, "tolerance": 0.035, "upright": true}
- seed 100005:  {"puck_to_target_xy": 0.1122, "tolerance": 0.035, "upright": true}
- seed 100006:  {"puck_to_target_xy": 0.101, "tolerance": 0.035, "upright": true}
- seed 100007:  {"puck_to_target_xy": 0.1142, "tolerance": 0.035, "upright": true}
