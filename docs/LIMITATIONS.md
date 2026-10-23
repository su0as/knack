# Limitations

Published on purpose. If a number in this repo looks too good, check it against this list.

## Simulation

- **Simplified arm.** The simulated arm has SO-101 proportions but is built from primitives with zero joint offsets and an idealised parallel gripper (the real SO-101 has one fixed and one moving jaw). Joint position control with gravity compensation is much better behaved than real hobby servos.
- **Perception is easy in sim.** `observe()` returns object centres and yaw with about 2 mm and 0.02 rad of Gaussian noise. A real overhead camera with colour thresholding will be noisier, can miss objects and has no height information.
- **Narrow task family.** Six tabletop scenes with cubes, a puck, a target circle and trays. No articulated objects, deformables, clutter or tool use. Success on these says nothing about long-horizon household tasks.
- **Domain randomisation is light**: object mass +/-25%, friction +/-15%, grip force 5-7 N, positions and yaw. No lighting, camera pose or actuator-delay randomisation.
- **Ground-truth checks are thresholds** (for example "red cube centre at least 5 cm above the table"). Borderline cases near a threshold can flip.

## The loop

- **Zero demonstrations, not zero priors.** The coder's prompt contains an API doc with gripper geometry and a short task-agnostic "perceive, act, verify, recover" guideline. That is engineering knowledge, not demonstrations, but it is help.
- **Held-out means unseen layouts of the same scene**, not unseen tasks.
- **Small practice batches** (default 8 episodes per round) give noisy round scores; the best round is chosen on that noisy score. The held-out evaluation (default 100 layouts, Wilson 95% CI) is the number to trust.
- **The vision judge can be wrong.** It sees 4 low-resolution frames. It abstains below a confidence threshold, and abstentions count as failures during practice. Its accuracy is measured against ground truth (`knack exp judge`) rather than assumed.
- **Custom instructions** (wording that differs from the scene's built-in task) have no ground truth, so both practice and evaluation rely on the judge only. The card says so.
- **Cost receipts** use catalogue prices from 23 Oct 2026 and the token counts returned by the API. Mock runs estimate tokens from characters and are labelled as mock.

## Safety and isolation

- The sandbox is a **guardrail, not a security boundary**: AST allowlist, restricted builtins, import allowlist, one process per episode, wall-clock kill. Do not run code from untrusted models outside a container.
- The safety layer checks Cartesian targets, joint limits, speeds, elbow clearance and gripper-table force in sim. On the real arm there is no force sensing; a hardware e-stop is still required.

## Untested paths (as of 23 Oct 2026)

- **Real SO-101 backend** (`knack/real/`): written against LeRobot's SO-101 follower API, never run on hardware. Joint sign/offset defaults are placeholders.
- **Nebius Serverless Jobs backend** (`knack/nebius.py`): written from the Nebius CLI docs, not yet run (it is paid usage). Job status parsing is defensive because the JSON schema was not verified.
- **Live Nemotron runs**: the pipeline is tested end to end with a mock coder in CI; real model behaviour (code quality, format compliance, cost) is unmeasured until the pilot runs.
