# Skill card: Push puck

**Task:** Push the orange puck so that its centre ends up inside the green circle. The puck is too wide to grasp.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 2 rounds, 16 episodes; best version from round 2
- Held-out success (ground truth): **49/50 = 98%** (Wilson 95% CI 90% to 100%)
- Safety layer: 0 halts, 0 clamps over 50 episodes
- OpenCV perception on held-out episodes: 100/100 object sightings (100%), median per-episode position error 0.41 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 4 | 10,677 | 5,994 | $0.0086 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 1 | 5,237 | 424 | $0.0004 |
| compute | local | | | 158 s | $0.0000 |
| **total** | | 5 | 15,914 | 6,418 | **$0.0090** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0037 |
| 2 | 8/8 | 0 | $0.0090 |

## Failure gallery (held-out)

- seed 100035:  {"puck_to_target_xy": 0.0395, "tolerance": 0.035, "upright": true}
