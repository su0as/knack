# Skill card: Into the tray

**Task:** Put the yellow cube into the tray and let go of it.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **49/50 = 98%** (Wilson 95% CI 90% to 100%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/Nemotron-3-Ultra-550b-a55b` | 1 | 1,684 | 1,090 | $0.0050 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 96 s | $0.0000 |
| **total** | | 1 | 1,684 | 1,090 | **$0.0050** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0050 |

## Failure gallery (held-out)

- seed 100035:  {"yellow_cube_tray_dx": 0.0029, "yellow_cube_tray_dy": 0.1106, "yellow_cube_z": 0.0149, "yellow_cube_held": false}
