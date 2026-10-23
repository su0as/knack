**Mode 1: Premature release (2 episodes: 2002, 2005)**
*Root cause:* The robot releases the red cube at approach height (z=0.08m) before descending to stacking height. The release command occurs at lines 56 and 56 in both traces, while the stack descent (line 82) never executes.
*Fix:* Move the `robot.release()` call to after the `safe_move` to `stack_z` (line 82), ensuring the cube is lowered onto the blue cube before opening gripper.

**Mode 2: Insufficient stack clearance (2 episodes: 2002, 2005)**
*Root cause:* `z_gap` is 0.0 in failures, meaning the red cube sits flush on the blue cube with no vertical gap. The stacking height formula (line 81) uses `blue_pos[2] + CUBE_SIZE + EPS`, but if the blue cube pose is stale or the red cube penetrates the blue cube during descent, collision or unstable stacking occurs.
*Fix:* Increase `EPS` from 0.001 to 0.01 on line 81 to guarantee positive clearance, and re-observe blue pose immediately before the stack descent (after line 68) to capture any drift.