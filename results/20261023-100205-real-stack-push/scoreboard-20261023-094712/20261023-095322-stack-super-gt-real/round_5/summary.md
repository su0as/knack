**Mode 1: XY mis‑alignment during stack (2 episodes)**
- **Root cause:** After lifting the red cube, the code re‑observes the blue cube (line 78‑81) but then moves to the *observed* blue pose (line 84). The observed pose can drift relative to the original base pose, causing the robot to lower the red cube into empty space instead of on the blue cube.
- **Fix:** Use the original `blue_pos` from the initial observation (line 10) for the stack‑height move, or re‑observe after the red cube is lifted and before the stack move.

**Mode 2: Premature release before stacking (2 episodes)**
- **Root cause:** The release step (line 122) executes immediately after the stack height check (line 99‑116) without ensuring the robot is correctly positioned over the blue cube. In seed 5004/5005 the gripper releases at z=0.015 (blue height) while the red cube is still above, causing a collision or missed stack.
- **Fix:** Move the `robot.release()` call to after the retreat step (line 130‑133), or add a `safe_move` to `ABOVE_Z` immediately before release.

**Mode 3: Grasp/hold loss (2 episodes)**
- **Root cause:** The grasp succeeds (line 59) but `holding()` returns `"red_cube"` only transiently; the subsequent lift (line 71) or corrective move (line 55) drops the cube, and the release‑check (line 124) fails.
- **Fix:** Increase the corrective move speed or add a verification `robot.holding() == "red_cube"` after line 55 before proceeding to lift.