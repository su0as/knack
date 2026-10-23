**Mode 1: XY offset miss (5 episodes: 1000, 1002, 1004, 1006, 1008)**
*Root cause:* The approach to the red cube uses `red_pos` from the initial observation (line 6-7). If the cube shifts or is mis-detected, the robot aims at the wrong XY coordinates. The subsequent stack move (line 51) uses fresh `blue_pos` (line 43-44), but the red cube is already misplaced, causing a collision or missed stack.
*Fix:* Re-observe the red cube pose immediately before the final approach to the stack (insert after line 44: `red_pos = obs["objects"]["red_cube"]["pos"]` and use `red_pos` for the `move_to` on line 51).

**Mode 2: Z-gap / release timing (2 episodes: 1001, 1003, 1005, 1007 — actually these are successes; failures have z_gap ≈ 0.0)**
*Root cause:* Failed episodes show `z_gap=0.0` (line 55 descent hits blue cube top). The release (line 61) occurs at `stack_z=0.045`, but if the robot descends slightly too far or the blue cube is taller, the red cube contacts the blue before release, jamming the gripper.
*Fix:* Add a small Z clearance check before release: after line 55, verify `pos.z > stack_z + 0.005`; if not, retreat to `stack_z + 0.01` before releasing.