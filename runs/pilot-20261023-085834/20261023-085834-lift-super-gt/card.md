# Skill card: Lift

**Task:** Pick up the red cube and hold it at least 5 cm above the table.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Practice: 3 rounds, 24 episodes; best version from round 3
- Held-out success (ground truth): **50/50 = 100%** (Wilson 95% CI 93% to 100%)
- Safety layer: 0 halts, 15 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 4 | 11,920 | 7,877 | $0.0107 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 2 | 7,446 | 748 | $0.0006 |
| compute | local | | | 114 s | $0.0000 |
| **total** | | 6 | 19,366 | 8,625 | **$0.0113** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 0/8 | 0 | $0.0020 |
| 2 | 6/8 | 0 | $0.0081 |
| 3 | 8/8 | 0 | $0.0113 |
