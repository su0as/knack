# Feedback: Nebius Token Factory, Nebius AI Cloud, NVIDIA models

Draft, started 23 Oct 2026. Each item says what we did, what happened and how to reproduce it. Items marked TODO get filled in from real runs.

## Nebius Token Factory

**Used for:** every model call in Knack (coder, trace summariser, vision judge, baseline).

What worked well
- OpenAI-compatible API: the official `openai` Python SDK worked by changing `base_url` and the key. Zero custom client code.
- The model catalogue shows price per million input, cached and output tokens on each card, which made it easy to put a dollar receipt on every skill.
- TODO: latency and reliability observed during the pilot.

What needs work
1. **Physical-AI models are dedicated-endpoint only.** `Cosmos3-Super-Reasoner`, `Nemotron-3-Nano-Omni` and `Nemotron-Nano-V2-12b` show "public endpoint: not available". For a hackathon focused on Physical AI, the physics-reasoning model being unavailable per token pushed us to use a general vision model as the success judge. Repro: Model catalog, open the Cosmos3 card.
2. **Catalogue labels Nemotron 3 Nano Omni as text-to-text**, which contradicts the name and model description. Repro: Model catalog, Nano Omni card, Modality field.
3. **Sample code uses different regional base URLs per model** (for example `api.tokenfactory.us-central1.nebius.com` for Nemotron 3 Ultra and Super, `us-north1` for Nemotron 3.5 Super VL, the global `api.tokenfactory.nebius.com` for Lightning and Nano), while the card says "Region is global and may change at any time". It is unclear whether one global base URL is safe for all models. Knack works around it by trying the global URL and falling back to the card's regional URL on 404. Repro: open the "Set up and chat as code" sample on the Ultra, Super VL and Lightning cards.
4. **Model ID casing is inconsistent**: `nvidia/Nemotron-3-Ultra-550b-a55b`, `nvidia/nemotron-3-super-120b-a12b` (lower case), `nvidia/Nemotron-3_5-Lightning` (underscore) next to `nvidia/Nemotron-3.5-Super-VL` (dot). Easy to get a 404 by typing the display name.
5. TODO: anything found in the pilot (rate limits, reasoning-token accounting, tool calling, image input limits).

Onboarding (zero to hello world): TODO, time it during the first real call.

Would we build with it again? TODO after the pilot.

## Nebius AI Cloud (Serverless Jobs)

**Used for:** optional parallel practice backend (`--backend nebius`), one CPU job per practice round.

What needs work
1. **Hackathon credits do not cover AI Cloud.** The promo credits apply to Token Factory only, so Serverless Jobs are real spend for participants. A small AI Cloud credit would let Physical AI teams use the jobs product the track is built around.
2. **Minimum job timeout is 1 hour** (`--timeout` minimum `1h`). Fine for billing (jobs are billed while running), but surprising for 3-minute batch jobs.
3. **Injected files are limited to 64 KiB**, so a source tarball cannot be injected; Knack uploads it to Object Storage instead, which adds a bucket and access-key setup step before the first job.
4. TODO: time from `nebius ai job create` to the container starting, and log availability.

## NVIDIA models

| Model | Used for | Notes (TODO from runs) |
|---|---|---|
| Nemotron 3 Ultra 550B-A55B | coder | code quality, format compliance, reasoning tokens per round, $ per skill |
| Nemotron 3 Super 120B-A12B | cheaper coder | same, compared with Ultra |
| Nemotron 3 Nano 30B-A3B | scoreboard | can a 3B-active model program a robot at all? |
| Nemotron 3.5 Lightning | trace summariser | does it cite the right code lines? |
| Nemotron 3.5 Super VL | vision judge | accuracy and abstention vs ground truth, false-success rate |
