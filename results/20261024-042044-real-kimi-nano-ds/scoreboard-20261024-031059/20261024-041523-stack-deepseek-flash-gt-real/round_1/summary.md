**Mode 1: Off-target placement (2 episodes: 1001, 1003)**
*Root cause:* The robot releases the red cube at the *blue* cube's XY position (`place_x = bx - off_x`, `place_y = by - off_y`), but the blue cube drifts during the approach. In seed 1001, the release lands at (0.126, 0.016) while the blue cube is at (0.137, 0.010), causing a 4.3 cm lateral offset. The `off_x/off_y` calibration (lines 83–101) assumes static cubes.
*Fix:* Freeze the blue cube pose at lift start and use that pose for placement coordinates, or add a final `robot.move_to(blue_x, blue_y, 0.05)` before release to re-center over the blue cube.

**Mode 2: Premature release / drop (3 episodes: 1005, 1006, 1007)**
*Root cause:* The robot releases the red cube while translating away from the stack (line 115) without verifying the gripper is directly above the target. In seed 1005, the red cube ends at z=0.045 but x/y are offset by ~0.038 m, indicating a side-slip during the release trajectory.
*Fix:* After `robot.release()` (line 115), insert a brief `robot.move_by(dz=0.02, speed=0.1)` to lift clear *before* the final retreat move (line 117), ensuring gravity does not pull the cube sideways.