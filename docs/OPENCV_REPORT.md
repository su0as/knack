# Knack: robots that learn a skill by practising, seeing the scene through OpenCV 5

Technical report for the OpenCV AI Competition 2026 (powered by AWS). Team: Suhas Suren (NTU Singapore, MSc Robotics).
Code: https://github.com/su0as/knack. Every number below is read from a file in the repository (`results` branch);
the source is named next to each table.

## 1. Problem and users

Teaching a robot arm a new tabletop task today means either an engineer hand-coding and tuning it for days, or someone
recording 50 to 200 teleoperated demonstrations to train a policy. Both are out of reach for small labs, classrooms and
makers with a cheap open arm. Knack takes a third route: a coding agent writes the robot's program, simulated robots
practise it on many randomised layouts, the failures are analysed, the program is rewritten, and the best version is
verified on unseen layouts. Zero demonstrations. The output is a plain Python skill that runs without any model in the
control loop, inside a fixed safety layer.

Users: robotics students and small teams who need a working pick, place, push, stack or sort skill on a low-cost arm,
and need to know how well it works before trusting it.

## 2. Where OpenCV 5 does the work

In vision mode (`--realism vision`) the robot never reads object poses from the simulator. Every `observe()` and
`get_pose()` call goes through an OpenCV 5 perception pipeline on rendered RGB-D frames (`knack/vision.py`):

1. Capture RGB and depth from an overhead camera (front camera as backup), with a sensor model: depth noise growing with
   distance squared, 1 mm depth quantisation, RGB noise, and a per-episode extrinsic calibration error that the pipeline
   does not know about.
2. `cv2.cvtColor` to HSV, `cv2.inRange` colour masks for the scene palette, `cv2.morphologyEx` opening.
3. `cv2.connectedComponentsWithStats` to separate blobs; candidates are taken largest first and rejected if their
   footprint is larger than the object could be (this is how same-coloured tray walls are not mistaken for the cube).
4. Back-projection of every mask pixel to 3D with the pinhole intrinsics and camera pose; points on same-coloured
   fixtures are removed geometrically.
5. Top-face selection by height, then `cv2.minAreaRect` in the table plane for centre and yaw.
6. Static fixtures (target circles, trays) are mapped once per episode; a tray's centre comes from its wall-top ring.
7. Objects that neither camera can see (typically under the gripper) are missing from the observation and `get_pose()`
   raises `LookupError`.

The pipeline's output is the only thing the robot's program knows about the world, so OpenCV's detections decide every
grasp point, approach yaw and verification step.

## 3. The agentic loop (perception, decision, action)

```mermaid
flowchart LR
  T[task text] --> C1[Coder LLM writes skill.py]
  C1 --> P[Practice: 8 randomised layouts in parallel]
  P --> V[OpenCV 5 perception on every look<br/>RGB-D, HSV masks, components, minAreaRect]
  V --> A[Skill acts: move, grasp, verify, re-look]
  A --> V
  A --> S{Score episodes}
  S -->|below target| L[Trace summariser: failure modes with line numbers,<br/>perception sightings and errors]
  L --> C2[Coder rewrites the skill]
  C2 --> P
  S -->|best version| E[Re-check top versions on 16 fresh layouts,<br/>then held-out eval on 50 unseen layouts]
  E --> K[Skill card: success + 95% CI, cost receipt, perception stats]
```

OpenCV output changes later actions at two levels:
- **Inside an episode:** the skill observes, acts, re-observes and branches on what it sees (for example, if the cube is
  not visible because the gripper hides it, the skill moves away and looks again; if a placed cube is not where it should
  be, it retries).
- **Across practice rounds:** each episode's perception record (sightings, misses, median error) is fed back to the
  coder with the failure analysis, so the next version of the program changes how and when it looks.

## 4. AWS deployment

```mermaid
flowchart LR
  J[Judge's browser] -->|HTTP 80| EC2[EC2 t4g.medium, Graviton, Ubuntu 24.04 arm64<br/>Knack console + practice runs<br/>OpenCV 5 + MuJoCo, OSMesa]
  EC2 -->|GetParameter| SSM[(SSM Parameter Store<br/>SecureString: model key, passcode)]
  EC2 -->|sync every 10 min| S3[(S3 bucket: run summaries)]
  EC2 -->|HTTPS| TF[Nebius Token Factory<br/>coder and summariser models]
  Admin -->|Session Manager, no SSH| EC2
```

- One Arm (Graviton) instance runs both the console and the practice episodes; the OpenCV 5 and MuJoCo work runs there.
- Secrets live in SSM Parameter Store as SecureString and are read once at boot; nothing secret is in the repository,
  the image or the user data. No SSH port: administration is through Session Manager.
- Public console: anyone can browse every run, frame by frame. Starting a new run spends model credits, so it needs a
  passcode (given in the testing instructions), is capped at $0.10, and only one run can start every two minutes.
- Cost guardrails: Free account plan (credits only), AWS Budgets alerts at $1, $5 and $10, one region, no autoscaling.
- Reproduce: `deploy/aws/README.md` and `deploy/aws/user-data.sh`.

## 5. Evaluation

### 5.1 Perception accuracy (OpenCV 5 vs simulator ground truth)

[[perception_bench.md table]]

### 5.2 Skills learned with OpenCV perception

[[vision scoreboard table]]

### 5.3 What practice adds

[[gain table for vision runs]]

## 6. Failure cases and limitations

- Simulated cameras: even with the sensor model, rendered images are cleaner than a real camera (no motion blur, no
  specular highlights, no lighting changes). Real-camera validation on an SO-101 arm is the next step; the overhead
  pipeline for the real arm (`knack/real/vision.py`) uses the same OpenCV steps with a homography.
- Colour-based segmentation assumes a known palette. Unknown objects would need a learned detector (OpenCV 5's DNN
  engine is the natural next step).
- Occlusion: when the gripper hides an object, the object is missing; skills must handle it. Some first-version skills
  do not, which is one of the failure modes practice fixes.
- The coder model can write skills that regress; Knack keeps the best version and re-checks it on fresh layouts.
- Vision-model success judges (tested separately) can be fooled when the success criterion is not visible (for example
  "at least 5 cm above the table"); the ground-truth check is kept wherever one exists.

## 7. Responsible use

- Zero demonstrations and no personal data: the system never records people.
- The learned skill runs inside a deterministic safety layer (workspace box, joint and speed limits, table-force limit)
  that AI-written code cannot catch or override. A real arm still needs a hardware emergency stop.
- AI-written code runs in a guardrail sandbox (AST allowlist, restricted builtins, one process per episode, wall-clock
  kill); it is not a security boundary, so the public demo never runs code from visitors.
- Costs are bounded at every level: per-run budget caps, a passcode for the public demo, and AWS budget alerts.
