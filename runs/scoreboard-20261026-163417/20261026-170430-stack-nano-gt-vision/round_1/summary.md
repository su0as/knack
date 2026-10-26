**Mode 1: Premature release (5 episodes)**
*Root cause:* The skill releases the red cube at `place_z = blue_z + 2*half_h` (line 41), but the robot moves to this pose and releases *before* the cube settles on top of the blue cube. The final positions show the red cube at `z=0.015` (same height as blue), indicating it never lifted above the target.
*Fix:* Increase `place_z` by an additional safety margin (e.g., `+ 0.02`) before the `move_to` call at line 79, allowing the gripper to descend slowly after arrival.

**Mode 2: XY misalignment (4 episodes)**
*Root cause:* The place pose uses `place_x, place_y = blue_x, blue_y` (line 42) without accounting for the red cube’s offset. The `xy_offset` values (0.03–0.066 m) exceed the cube side (0.03 m), causing the red cube to land beside the blue one.
*Fix:* Shift the place pose by half the red cube’s width in the direction of the gripper approach (e.g., `place_x = blue_x + 0.015`) before the `move_to` at line 79.

**Mode 3: Grasp failure (2 episodes)**
*Root cause:* The verification loop (lines 60–72) retries grasp only 3 times. If the initial `grasp()` at line 56 fails to enclose the cube (common with pose error > 2 cm), the loop exhausts and returns `False` at line 72.
*Fix:* Increase `max_retries` to 5 and add a `robot.wait(0.2)` after each `robot.release()` at line 65 to let the simulation reset before re‑approaching.