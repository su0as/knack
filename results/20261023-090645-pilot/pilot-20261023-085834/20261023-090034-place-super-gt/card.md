# Skill card: Place in circle

**Task:** Put the blue cube inside the green circle on the table and let go of it.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **50/50 = 100%** (Wilson 95% CI 93% to 100%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `nvidia/nemotron-3-super-120b-a12b` | 2 | 4,000 | 3,185 | $0.0041 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 99 s | $0.0000 |
| **total** | | 2 | 4,000 | 3,185 | **$0.0041** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0041 |
