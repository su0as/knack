# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 6 rounds, 48 episodes; best version from round 4
- Held-out success (ground truth): **28/50 = 56%** (Wilson 95% CI 42% to 69%)
- Safety layer: 0 halts, 0 clamps over 50 episodes
- OpenCV perception on held-out episodes: 176/176 object sightings (100%), median per-episode position error 3.79 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/Nemotron-3-Ultra-550b-a55b` | 7 | 29,283 | 29,394 | $0.1175 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 5 | 27,523 | 1,748 | $0.0021 |
| compute | local | | | 512 s | $0.0000 |
| **total** | | 12 | 56,806 | 31,142 | **$0.1195** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0055 |
| 2 | 0/8 | 6 | $0.0213 |
| 3 | 1/8 | 0 | $0.0438 |
| 4 | 5/8 | 0 | $0.0636 |
| 5 | 5/8 | 0 | $0.0984 |
| 6 | 4/8 | 0 | $0.1195 |

## Failure gallery (held-out)

- seed 100002:  {"puck_to_target_xy": 0.0483, "tolerance": 0.035, "upright": true}
- seed 100007:  {"puck_to_target_xy": 0.0573, "tolerance": 0.035, "upright": true}
- seed 100008:  {"puck_to_target_xy": 0.0748, "tolerance": 0.035, "upright": true}
- seed 100012:  {"puck_to_target_xy": 0.0623, "tolerance": 0.035, "upright": true}
- seed 100013:  {"puck_to_target_xy": 0.0796, "tolerance": 0.035, "upright": true}
- seed 100014:  {"puck_to_target_xy": 0.0537, "tolerance": 0.035, "upright": true}
- seed 100016:  {"puck_to_target_xy": 0.0784, "tolerance": 0.035, "upright": true}
- seed 100019:  {"puck_to_target_xy": 0.0511, "tolerance": 0.035, "upright": true}
