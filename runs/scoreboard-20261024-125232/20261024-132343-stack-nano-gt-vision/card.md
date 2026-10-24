# Skill card: Stack

**Task:** Stack the red cube on top of the blue cube and let go.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 3 rounds, 24 episodes; best version from round 3
- Held-out success (ground truth): **49/50 = 98%** (Wilson 95% CI 90% to 100%)
- Safety layer: 0 halts, 0 clamps over 50 episodes
- OpenCV perception on held-out episodes: 100/100 object sightings (100%), median per-episode position error 0.03 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 3 | 10,712 | 13,982 | $0.0040 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 2 | 9,179 | 646 | $0.0007 |
| compute | local | | | 144 s | $0.0000 |
| **total** | | 5 | 19,891 | 14,628 | **$0.0047** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0008 |
| 2 | 0/8 | 8 | $0.0034 |
| 3 | 8/8 | 0 | $0.0047 |

## Failure gallery (held-out)

- seed 100021:  {"xy_offset": 0.0265, "z_gap": 0.0333, "red_held": false, "blue_z": 0.02}
