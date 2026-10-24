# Skill card: Lift

**Task:** Pick up the red cube and hold it at least 5 cm above the table.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 2 rounds, 16 episodes; best version from round 2
- Held-out success (ground truth): **50/50 = 100%** (Wilson 95% CI 93% to 100%)
- Safety layer: 0 halts, 0 clamps over 50 episodes
- OpenCV perception on held-out episodes: 200/200 object sightings (100%), median per-episode position error 0.03 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 2 | 6,068 | 3,790 | $0.0013 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 1 | 4,452 | 427 | $0.0004 |
| compute | local | | | 123 s | $0.0000 |
| **total** | | 3 | 10,520 | 4,217 | **$0.0016** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0005 |
| 2 | 8/8 | 0 | $0.0016 |
