# Skill card: Stack

**Task:** Stack the red cube on top of the blue cube and let go.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 4 rounds, 32 episodes; best version from round 4
- Held-out success (ground truth): **49/50 = 98%** (Wilson 95% CI 90% to 100%)
- Safety layer: 0 halts, 41 clamps over 50 episodes
- OpenCV perception on held-out episodes: 300/300 object sightings (100%), median per-episode position error 3.9 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 4 | 16,998 | 11,119 | $0.0037 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 3 | 17,011 | 1,037 | $0.0013 |
| compute | local | | | 306 s | $0.0000 |
| **total** | | 7 | 34,009 | 12,156 | **$0.0050** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0007 |
| 2 | 2/8 | 0 | $0.0022 |
| 3 | 0/8 | 0 | $0.0034 |
| 4 | 8/8 | 0 | $0.0050 |

## Failure gallery (held-out)

- seed 100001:  {"xy_offset": 0.0348, "z_gap": 0.0, "red_held": false, "blue_z": 0.0149}
