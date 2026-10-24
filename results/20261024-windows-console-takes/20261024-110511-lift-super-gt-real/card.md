# Skill card: Lift

**Task:** Pick up the red cube and hold it at least 5 cm above the table.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 3 rounds, 24 episodes; best version from round 3
- Held-out success (ground truth): **50/50 = 100%** (Wilson 95% CI 93% to 100%)
- Safety layer: 0 halts, 3 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 3 | 10,356 | 5,511 | $0.0077 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 2 | 8,222 | 748 | $0.0007 |
| compute | local | | | 287 s | $0.0000 |
| **total** | | 5 | 18,578 | 6,259 | **$0.0084** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0012 |
| 2 | 6/8 | 0 | $0.0043 |
| 3 | 8/8 | 0 | $0.0084 |
