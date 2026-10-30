**Mode 1: Insufficient lift height** (6 episodes)
- **Root cause:** `GRASP_HEIGHT + LIFT_HEIGHT` (line 57) computes 0.015 + 0.05 = 0.065 m, but the actual lift stops at ~0.0643–0.0645 m. The 5 cm target is not reached due to floating‑point or controller rounding.
- **Fix:** Change `LIFT_HEIGHT = 0.055` (5.5 cm) to guarantee clearance, or add a post‑lift `robot.wait(0.1)` and re‑check `robot.holding()` before returning.

**Mode 2: Grasp succeeds but cube drops on lift** (all 8 episodes)
- **Root cause:** After `robot.grasp()` (line 48) the gripper closes, yet the subsequent `move_to` to lift height (line 58) may lose contact if the grasp pose is slightly off‑center or the robot speed is too high (line 59: `speed=0.15`).
- **Fix:** Reduce lift speed to `0.08` (matching the descent speed on line 40) and/or add a brief `robot.wait(0.05)` after `robot.grasp()` before the first move.

**Mode 3: Perception‑to‑pose mismatch** (2 episodes)
- **Root cause:** `get_red_pose()` (line 12) returns pose with `z≈0.016` (cube centre), but the code uses this `z` for `above_pos` (line 29: `0.10`) and `grasp_pos` (line 38). If the cube is tilted or the camera offset is uncalibrated, the robot descends to a slightly wrong height, causing grasp failure or slippage.
- **Fix:** Offset the grasp height explicitly: `grasp_pos_z = pose['pos'][2] + GRASP_HEIGHT` (line 38) instead of assuming `GRASP_HEIGHT` aligns with the returned `z`.