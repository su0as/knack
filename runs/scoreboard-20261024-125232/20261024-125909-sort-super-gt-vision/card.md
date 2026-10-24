# Skill card: Sort by colour

**Task:** Put the red cube into the red tray and the blue cube into the blue tray.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **50/50 = 100%** (Wilson 95% CI 93% to 100%)
- Safety layer: 0 halts, 100 clamps over 50 episodes
- OpenCV perception on held-out episodes: 503/504 object sightings (100%), median per-episode position error 0.03 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 1 | 1,818 | 1,923 | $0.0023 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 135 s | $0.0000 |
| **total** | | 1 | 1,818 | 1,923 | **$0.0023** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0023 |
