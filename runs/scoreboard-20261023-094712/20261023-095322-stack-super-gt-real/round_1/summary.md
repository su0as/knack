**Mode 1: Premature release (55 episodes)**
*Root cause:* Release occurs at `stack_z` (blue top), but the red cube is held at `GRASP_Z` (middle). The vertical gap between gripper tip and blue top is only `GRASP_Z - stack_z ≈ -0.015m`, causing the red cube to collide with or rest on the blue cube before release triggers. The robot releases while still contacting the blue cube, dropping the red cube beside it.
*Fix:* Lower the release target to `blue_pos[2] + GRASP_Z` (blue center) so the red cube clears the blue top. Change line 55’s `robot.release()` position context or adjust `stack_z` calculation to `blue_pos[2] + GRASP_Z`.

**Mode 2: XY misplacement (30 episodes)**
*Root cause:* The `move` calls for the blue cube use `blue_pos` from the initial observation. If the blue cube shifted slightly during the red cube lift, the robot aims at an outdated pose. The `xy_offset ≈ 0.03m` error in checks confirms systematic aiming error.
*Fix:* Re-observe the blue cube pose immediately before the stack move (after red lift, before line 50) and use that fresh pose for all subsequent blue moves.