# OpenCV AI Competition 2026: submission text for Knack

Fill in the three [[...]] placeholders before submitting.

## Project name
Knack

## Elevator pitch (one line)
A robot arm that teaches itself a new task by practising in simulation, seeing the scene only through OpenCV 5, with zero demonstrations.

## Special award
Agentic Vision. OpenCV output decides every grasp and changes the next action inside an episode (look again when the gripper hides the object, verify and correct) and across practice rounds (perception records feed the rewrite).

## About the project

### Inspiration
Teaching a cheap robot arm a new tabletop task still means days of hand-coding or 50 to 200 teleoperated demonstrations. Small labs, classrooms and makers have neither. We wanted to know whether a robot could get a working, measured skill from one sentence of instructions and its own practice.

### What it does
You type a task ("put the red cube in the red tray and the blue cube in the blue tray"). A coding model writes a short Python program for the arm. Simulated arms practise it on 8 randomised layouts in parallel. Every look the program takes goes through an OpenCV 5 RGB-D perception pipeline, not simulator state. Failed episodes are analysed into failure modes with line numbers, the program is rewritten, and the best version is checked again on fresh layouts and then evaluated on 50 unseen layouts. You get a skill card: success rate with a 95% interval, perception accuracy, and a cost receipt in cents. The learned skill is plain code that runs with no model in the loop, inside a safety layer the AI-written code cannot override.

### How we built it
- Perception (`knack/vision.py`): RGB and depth from an overhead and a front camera, with a realistic sensor model (depth noise growing with distance squared, 1 mm quantisation, RGB noise, an unknown per-episode calibration error). OpenCV 5: HSV conversion and `inRange` masks, morphological opening, `connectedComponentsWithStats` with size gating, back-projection of mask pixels to 3D, top-face selection, `minAreaRect` for centre and yaw, fixtures mapped once per episode. Hidden objects are reported as missing, never guessed.
- Learning loop: Nemotron coder models on Nebius Token Factory write and rewrite the skill; a smaller model summarises failure traces; revert-to-best plus a re-check on 16 fresh layouts stops noisy practice scores from picking a bad version.
- Simulation: MuJoCo arm and scenes (lift, place, push, stack, tray, sort) with layout randomisation.
- AWS: one Graviton (t4g) EC2 instance runs the console and the practice episodes (OpenCV and MuJoCo on Arm), secrets from SSM Parameter Store, run summaries synced to S3, Session Manager instead of SSH, budget alerts, Free plan. The public console lets anyone browse every run frame by frame; starting a new run needs a passcode and is capped at $0.10.

### Results (all in the repo)
- Perception benchmark, 30 layouts per scene, 180 layouts: 100% detection on first look, median position error 4.3 to 4.5 mm, worst case under 10 mm, yaw error under 0.5 degrees. During manipulation 97% to 100% of looks find the object; the misses are gripper occlusion.
- Skills learned with OpenCV perception, 50 unseen layouts each: Nemotron 3.5 Super 42/50 lift, 48/50 push, 50/50 stack, 49/50 sort for $0.038 in total. Practice matters: Super lift went 0/8, 0/8, 4/8, 8/8 across practice rounds; Nano stack 0/8 to 8/8.
- Honest failures: Ultra reaches only 28/50 on push; Nano never learns lift, push or sort; a vision-model judge was fooled by lifts a few millimetres short, so ground truth is kept wherever one exists.

### Challenges
Same-coloured fixtures (a blue tray wall looks like a blue cube) needed size gating and geometric rejection. A perfect render made perception look unrealistically good (under 0.3 mm), so we added a sensor model and calibration error. Practice scores on 8 layouts are noisy, which is why the best version is re-checked before evaluation.

### What we learned
Most first-try failures are not perception failures; they are the program not checking what it sees. The rewrites that work add looks: verify the grasp, look again when occluded, check the height after lifting.

### What's next
Real-camera validation on an SO-101 arm with the same OpenCV steps and a homography; OpenCV 5's DNN engine for objects outside a known colour palette.

## Built with
opencv, python, mujoco, numpy, aws-ec2, aws-graviton, aws-s3, aws-systems-manager, nebius-token-factory, nvidia-nemotron, github-actions

## Links
- Code: https://github.com/su0as/knack
- Live demo: [[http://<EC2 public IP>/]]
- Technical report: docs/OPENCV_REPORT.md (PDF attached)
- Video: [[YouTube URL]]

## Testing instructions (for judges)
Open the live demo link. Pick any run from the run picker to replay it: code per round, practice frames, failure analysis and the held-out evaluation. To start a new practice run, choose a task, set PERCEPTION to "camera + OpenCV 5", press Learn, and enter passcode [[passcode]] when asked. A run takes a few minutes. To run locally: `pip install -e .` then `python -m knack oracle all --realism vision` (no API key needed) or `python -m knack ui`.
