**Mode 1: XY misplacement (3 episodes: 1001, 1005, 1006)**
*Root cause:* The `grasp_cube` function moves to the cube’s observed pose without correcting for initial robot offset. When the red cube is not precisely at the origin, the subsequent `move_to(bx, by, ...)` on line 48 targets the blue cube’s pose from the *grasp position*, causing a drift. The release then lands offset.
*Fix:* After `robot.home()` (line 7), run a short `robot.move_by(dx=..., dy=...)` to align the gripper with the cube’s true world coordinates before grasping.

**Mode 2: Premature release (2 episodes: 1006, 1001)**
*Root cause:* `release()` is called at line 56 after descending to `target_z` (line 53). If the gripper’s approach trajectory (line 23) or grasp z-offset (line 27) mis-estimates the cube thickness, the red cube contacts the blue cube off‑center and slips off before the fingers fully open.
*Fix:* Increase the descent speed or add a brief `robot.move_by(dz=-0.01, speed=0.02)` on line 52 to ensure the red cube sits flush on the blue cube before `release()`.

**Mode 3: Large initial offset (2 episodes: 1001, 1005)**
*Root cause:* Episodes start with the robot at `home()` (line 7) but the observed poses already include world-frame positions. If the robot’s zero‑point shifts between episodes, the hard‑coded `approach_z = cz + 0.10` (line 21) may place the tool above or below the cube, causing grasp failure or mis‑stack.
*Fix:* Calibrate the robot zero‑point once per session and store the offset, or add a post‑home correction `robot.move_to(0, 0, 0.20)` before observing (after line 7).