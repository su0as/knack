**Mode 1: XY offset drift (3 episodes: 3002, 3004, 3006)**
*Root cause:* The code uses the *initial* `red_yaw` from pickup throughout the stack maneuver. As the robot transports the cube, the base pose reference drifts relative to the blue cube, causing misalignment at line 77 and 86. The `move_to` at line 77 targets `stack_x, stack_y` with the old `red_yaw`, missing the target.
*Fix:* Re-observe blue cube pose immediately before stacking (after lift) and re-compute `red_yaw` relative to the blue cube frame, or reset yaw to zero at line 77.

**Mode 2: Premature release / z-gap collision (2 episodes: 3002, 3004)**
*Root cause:* `release()` fires at line 93 while the red cube is still at `STACK_Z + STACK_CLEARANCE` (line 84-86). The cube descends during release, and the gripper opens before the cube seats on the blue cube (z_gap=0.0 in checks). This is exacerbated when the XY offset is large, causing the cube to collide with the blue cube edge and tip.
*Fix:* Add a descent check after line 86: only release if `robot.z() < STACK_Z + 0.01`; otherwise descend further (`move_by(dz=-0.01)`) before releasing at line 93.