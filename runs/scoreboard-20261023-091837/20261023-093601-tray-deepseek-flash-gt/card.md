# Skill card: Into the tray

**Task:** Put the yellow cube into the tray and let go of it.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **50/50 = 100%** (Wilson 95% CI 93% to 100%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `deepseek-ai/DeepSeek-V4.1-Flash` | 1 | 1,627 | 7,654 | $0.0094 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 102 s | $0.0000 |
| **total** | | 1 | 1,627 | 7,654 | **$0.0094** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0094 |
