# Skill card: Sort by colour

**Task:** Put the red cube into the red tray and the blue cube into the blue tray.

- Demonstrations used: **0**
- Reward during practice: `gt`
- Perception and physics: `real` (camera-grade noise, about 8 mm; wider mass, friction and grip randomisation)
- Practice: 1 rounds, 8 episodes; best version from round 1
- Held-out success (ground truth): **50/50 = 100%** (Wilson 95% CI 93% to 100%)
- Safety layer: 0 halts, 0 clamps over 50 episodes

## Receipt

| role | model | calls | tokens in | tokens out | USD |
|---|---|---|---|---|---|
| coder | `deepseek-ai/DeepSeek-V4.1-Flash` | 1 | 1,768 | 8,776 | $0.0107 |
| summarizer | `nvidia/Nemotron-3_5-Lightning` | 0 | 0 | 0 | $0.0000 |
| compute | local | | | 154 s | $0.0000 |
| **total** | | 1 | 1,768 | 8,776 | **$0.0107** |

## Rounds

| round | success | errors | cumulative USD |
|---|---|---|---|
| 1 | 8/8 | 0 | $0.0107 |
