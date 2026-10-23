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
| coder | `nvidia/nemotron-3-super-120b-a12b` | 4 | 14,938 | 6,306 | $0.0102 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 2 | 6,951 | 7,841 | $0.0023 |
| compute | local | | | 108 s | $0.0000 |
| **total** | | 6 | 21,889 | 14,147 | **$0.0125** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 2/8 | 0 | $0.0014 |
| 2 | 6/8 | 0 | $0.0088 |
| 3 | 8/8 | 0 | $0.0125 |
