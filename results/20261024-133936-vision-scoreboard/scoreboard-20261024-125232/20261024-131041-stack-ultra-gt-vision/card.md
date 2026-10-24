# Skill card: Stack

**Task:** Stack the red cube on top of the blue cube and let go.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `vision` (poses from OpenCV 5 on rendered RGB-D cameras; wider mass, friction and grip randomisation)
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **50/50 = 100%** (Wilson 95% CI 93% to 100%)
- Safety layer: 0 halts, 0 clamps over 50 episodes
- OpenCV perception on held-out episodes: 198/200 object sightings (99%), median per-episode position error 6.97 mm

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/Nemotron-3-Ultra-550b-a55b` | 1 | 1,652 | 1,578 | $0.0064 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 81 s | $0.0000 |
| **total** | | 1 | 1,652 | 1,578 | **$0.0064** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0064 |
