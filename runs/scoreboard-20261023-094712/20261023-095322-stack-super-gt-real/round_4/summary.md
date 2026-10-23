**Mode 1: Premature release (5 episodes: 4002, 4003, 4005, 4007 + 1 other)**
*Root cause:* Release triggered before reaching stacking height. In 4002/4003 the robot released at `z=0.080` (line 103) while the stack target was `z≈0.050` (line 91). The gripper opened too early, dropping the cube onto the blue cube instead of stacking it.
*Fix:* Move the `robot.release()` call to after line 92 (after reaching `stack_z`), not before. Ensure the robot is at stacking height before opening.

**Mode 2: Grasp failure / slippage (3 episodes: 4005, 4007 + 1 other)**
*Root cause:* `robot.grasp()` returned success but the cube was not securely held, likely due to insufficient approach speed or pose mismatch. Line 57 grasps without re-observing the red cube pose after the initial approach (lines 37–44). The subsequent re-observation at line 51–54 does not update the grasp pose.
*Fix:* After line 54 (re-observing red pose), pass the updated `red_pos` and `red_yaw` to a targeted approach before calling `robot.grasp()` at line 57, ensuring the gripper is correctly aligned over the cube.

**Mode 3: Positioning error at stack (2 episodes: 4002, 4003)**
*Root cause:* The `safe_move` to `stack_z` (line 91–92) undershot or overshot due to accumulated pose drift. In 4002 the final `z_gap` was 0.0; in 4003 it was -0.0, indicating the red cube contacted the blue cube at the wrong height or offset.
*Fix:* Add a post-move verification at line 92–93: `if abs(robot.get_z() - stack_z) > 0.01: robot.log("Stack height miss")` and retry the move once before proceeding to release.