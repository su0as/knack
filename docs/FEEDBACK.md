# Feedback: Nebius Token Factory, Nebius AI Cloud, NVIDIA models

Draft, started 23 Oct 2026. Each item says what we did, what happened and how to reproduce it. Items marked TODO get filled in from real runs.

## Nebius Token Factory

**Used for:** every model call in Knack (coder, trace summariser, vision judge, baseline).

What worked well
- OpenAI-compatible API: the official `openai` Python SDK worked by changing `base_url` and the key. Zero custom client code.
- The model catalogue shows price per million input, cached and output tokens on each card, which made it easy to put a dollar receipt on every skill.
- **Key creation was fast.** API keys page, "Create API key", optional name, Create: the key is shown once in a copyable field, then masked in the list (first few characters, `**`, last few). Default expiry is 5 years (key created 23 Oct 2026 expires 22 Oct 2031). Under a minute from login to a working key.
- **`GET /v1/models` is free and immediately useful**: with the new key the global base URL `https://api.tokenfactory.nebius.com/v1/` listed 28 models, including all five per-token NVIDIA models Knack uses (`nvidia/Nemotron-3-Ultra-550b-a55b`, `nvidia/nemotron-3-super-120b-a12b`, `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`, `nvidia/Nemotron-3_5-Lightning`, `nvidia/Nemotron-3.5-Super-VL`). That let us verify every model ID before spending a cent. `knack models --remote` wraps it.
- **Reliability in the first live session (23 Oct 2026, from a GitHub Actions runner):** 30+ chat completions across Nemotron 3 Super, Nemotron 3 Ultra, Nemotron 3.5 Lightning and Nemotron 3.5 Super VL, zero errors, zero retries, every call on the global base URL. Median latency per call: Super as coder 9.3 s (median 1,626 output tokens, 384 of them reasoning), Ultra as coder 8.2 s (2,532 output, 1,466 reasoning), Lightning as summariser with thinking off 4.1 s (461 output). Numbers from `results/*/ledger.jsonl`.
- **`usage` is detailed and honest:** `completion_tokens_details.reasoning_tokens` and `prompt_tokens_details.multimodal_tokens.image` are reported (4 judge frames at 320x240 = 1,088 image tokens). That made exact per-role receipts possible.
- **The thinking switch works per request:** `chat_template_kwargs: {"enable_thinking": false}` on Nemotron 3.5 Lightning cut a one-sentence answer from about 500 output tokens to 31, and on Nemotron 3.5 Super VL cut a 4-frame judge call from 2.4 s / ~500 tokens to 1.3 s / ~45 tokens.

What needs work
1. **Physical-AI models are dedicated-endpoint only.** `Cosmos3-Super-Reasoner`, `Nemotron-3-Nano-Omni` and `Nemotron-Nano-V2-12b` show "public endpoint: not available". For a hackathon focused on Physical AI, the physics-reasoning model being unavailable per token pushed us to use a general vision model as the success judge. Repro: Model catalog, open the Cosmos3 card.
2. **Catalogue labels Nemotron 3 Nano Omni as text-to-text**, which contradicts the name and model description. Repro: Model catalog, Nano Omni card, Modality field.
3. **Sample code uses different regional base URLs per model** (for example `api.tokenfactory.us-central1.nebius.com` for Nemotron 3 Ultra and Super, `us-north1` for Nemotron 3.5 Super VL, the global `api.tokenfactory.nebius.com` for Lightning and Nano), while the card says "Region is global and may change at any time". It is unclear whether one global base URL is safe for all models. Knack works around it by trying the global URL and falling back to the card's regional URL on 404. Repro: open the "Set up and chat as code" sample on the Ultra, Super VL and Lightning cards.
4. **Model ID casing is inconsistent**: `nvidia/Nemotron-3-Ultra-550b-a55b`, `nvidia/nemotron-3-super-120b-a12b` (lower case), `nvidia/Nemotron-3_5-Lightning` (underscore) next to `nvidia/Nemotron-3.5-Super-VL` (dot). Easy to get a 404 by typing the display name.
5. **The global `/models` list includes models whose sample code points at a regional URL** (Ultra and Super VL), which suggests the global URL serves them too, but nothing in the UI says so. A one-line note on each card ("global URL works / regional URL recommended for latency") would remove the guesswork.
6. **Cosmos3-Super-Reasoner does not appear in `/models` at all** for a per-token key (consistent with it being dedicated-only), so there is no way to discover from the API that it exists or how to get it.
7. **The trial badge ("Trial: $1.00 · 29 days") does not say what happens at $0**: hard stop or automatic billing. For participants told to avoid charges, that is the first question. Repro: header badge on any page right after sign-up.
8. **A reasoning model that hits `max_tokens` mid-thought returns the unfinished thought as `content`.** Nemotron 3.5 Lightning, default thinking, `max_tokens=4000`, a failure-analysis prompt: `finish_reason: length`, `completion_tokens: 4000`, and `content` began "Here's a thinking process:" with no answer. In normal calls the reasoning arrives in a separate field, so clients reasonably treat `content` as the answer. Please keep truncated reasoning in the reasoning field (and `content` empty) so clients do not show a half-thought as a result. Knack now detects this and turns thinking off for the summariser.
9. **The thinking switch is not documented on the model cards.** We found `chat_template_kwargs.enable_thinking` by trial. For agent builders this is the single biggest cost and latency lever (10x fewer tokens on short structured answers), so a line on each Nemotron card would help.
10. **Image-plus-reasoning judges can be overconfident.** Nemotron 3.5 Super VL with thinking on said "success, confidence 0.95" on four lift episodes whose cube was 1 mm below the 5 cm line. That is not a platform bug (1 mm is invisible at 320x240), but it is why Knack's judge abstains, and why we measure it against ground truth instead of trusting it.

Onboarding (zero to hello world): login to working key and verified model list in under 5 minutes (23 Oct 2026). First paid chat completion worked first time from CI with only `base_url` and the key changed in the OpenAI SDK.

Would we build with it again? Yes. A full learning run that turned a task sentence into a verified skill cost between $0.004 and $0.065 on Nemotron (pilot, 23 Oct 2026), which is cheap enough to run every experiment many times. The main ask is documentation: the thinking switch, regional versus global URLs, and what the trial does at $0.

## Nebius AI Cloud (Serverless Jobs)

**Used for:** optional parallel practice backend (`--backend nebius`), one CPU job per practice round.

What needs work
0. **Onboarding facts (24 Oct 2026):** sign-in with the same GitHub identity as Token Factory created a *separate* AI Cloud tenant (`default-project-eu-west2`) after a contact-details form and an email code. Before any job can run, Billing asks for full billing details and a card, and charges a **$25 top-up on submit**. The two $25 Token Factory promo codes from this hackathon could not be used there. For a student team that wants to try one 3-minute CPU job, a $25 card charge is the biggest barrier in the whole stack; a small AI Cloud trial credit (even $5) would remove it.
1. **Hackathon credits do not cover AI Cloud.** The promo credits apply to Token Factory only, so Serverless Jobs are real spend for participants. A small AI Cloud credit would let Physical AI teams use the jobs product the track is built around.
2. **Minimum job timeout is 1 hour** (`--timeout` minimum `1h`). Fine for billing (jobs are billed while running), but surprising for 3-minute batch jobs.
3. **Injected files are limited to 64 KiB**, so a source tarball cannot be injected; Knack uploads it to Object Storage instead, which adds a bucket and access-key setup step before the first job.
4. TODO: time from `nebius ai job create` to the container starting, and log availability.

## NVIDIA models

| Model | Used for | Notes (TODO from runs) |
|---|---|---|
| Nemotron 3 Ultra 550B-A55B | coder | Pilot: solved lift and place in round 1 and push at 90% held-out. Always returned a valid ```python block. Once regressed itself from 88% to 0% over three rewrites, which is why Knack now reverts to the best version. |
| Nemotron 3 Super 120B-A12B | cheaper coder | Pilot: 100% / 100% / 80% held-out on lift / place / push for $0.004 to $0.011 per skill, at a third of Ultra's price. Fewer reasoning tokens than Ultra (median 384 vs 1,466). |
| Nemotron 3 Nano 30B-A3B | scoreboard | can a 3B-active model program a robot at all? |
| Nemotron 3.5 Lightning | trace summariser | With thinking off: short, line-cited failure modes in about 4 s, for example "Mode 1: Height shortfall (6 episodes). Root cause: lift_z computed as cube_pos[2] + 0.05 (line 28)...". Episode counts inside a mode are sometimes off by one or two. With thinking on and a 4000-token cap: no answer at all (see item 8 above). |
| Nemotron 3.5 Super VL | vision judge | accuracy and abstention vs ground truth, false-success rate |
