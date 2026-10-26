# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 4 rounds, 32 episodes; best version from round 4
- Held-out success (ground truth): **48/50 = 96%** (Wilson 95% CI 87% to 99%)
- Safety layer: 0 halts, 0 clamps over 50 episodes
- OpenCV perception on held-out episodes: 100/100 object sightings (100%), median per-episode position error 4.74 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 6 | 20,364 | 10,790 | $0.0158 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 3 | 10,492 | 969 | $0.0009 |
| compute | local | | | 331 s | $0.0000 |
| **total** | | 9 | 30,856 | 11,759 | **$0.0167** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 7/8 | 0 | $0.0042 |
| 2 | 6/8 | 0 | $0.0068 |
| 3 | 7/8 | 0 | $0.0106 |
| 4 | 8/8 | 0 | $0.0167 |

## Failure gallery (held-out)

- seed 100011:  {"puck_to_target_xy": 0.0312, "tolerance": 0.035, "upright": false}
- seed 100022:  {"puck_to_target_xy": 0.0287, "tolerance": 0.035, "upright": true}
