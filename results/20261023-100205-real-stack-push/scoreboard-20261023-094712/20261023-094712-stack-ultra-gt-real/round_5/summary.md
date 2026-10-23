**Mode 1: Grasp failure (2 episodes: 5002, 5006)**
*Root cause:* `grasp()` returned `holding: null` at lines 38 and 50. The robot descended to `GRASP_Z` but the gripper failed to close or the cube was misaligned.
*Fix:* Add a pre-grasp alignment check. Before line 32, verify `red_pos` is within a 0.02m radius of the approach target. If not, re-observe and move_to again.

**Mode 2: Stack misplacement (2 episodes: 5007, 5002 xy_offset>0.03)**
*Root cause:* After transport to `LIFT_Z`, the robot moved to `stack_x, stack_y` using `blue_yaw` (line 95). The blue cube yaw drifted or was outdated, causing the final descent to miss the target location (xy_offset up to 0.077).
*Fix:* Re-observe the blue cube yaw immediately before line 95. Replace `blue_yaw` with the fresh `obs["objects"]["blue_cube"]["yaw"]` to ensure alignment matches the current pose.

**Mode 3: Release timing (1 episode: 5007)**
*Root cause:* `release()` at line 123 occurred while the arm was still translating downward (trace shows release at `t=8.1` after descending to `0.050`). The cube did not seat before release.
*Fix:* Move the `robot.wait(0.1)` at line 120 immediately after the descent verification (line 118), before the `robot.release()` at line 123. This ensures the cube is stationary before letting go.