**Mode 1: Height shortfall (6 episodes)**
- **Root cause:** `lift_z` computed as `cube_pos[2] + 0.05` (line 28) assumes the cube sits exactly on the table. When the cube is already elevated (e.g., `red_cube_z ≈ 0.064`), adding 0.05 yields ~0.114 m, but the verification check at line 50 compares against `lift_z - 0.002`. The robot stops at `lift_z`, yet the observed cube height (~0.064 m) falls short of the required 0.065 m threshold.
- **Fix:** Set `lift_z = max(cube_pos[2] + 0.05, 0.065)` to enforce the absolute 5 cm‑above‑table requirement regardless of initial cube pose.

**Mode 2: Grasp opening too wide (2 episodes)**
- **Root cause:** `grasp()` at line 40 closes fingers to ~0.026 m opening. If the cube is tilted or offset, the gripper may not fully enclose it, causing the subsequent lift to drop the object before reaching `lift_z`.
- **Fix:** Add a pre‑grasp alignment step: `robot.move_to(cube_pos[0], cube_pos[1], cube_pos[2] + 0.02, yaw=cube_yaw, speed=0.02)` just before `grasp()` to ensure perpendicular approach.

**Mode 3: Motion error on descent (1 episode)**
- **Root cause:** `move_to` to `grasp_z` (line 37) at speed 0.05 (line 38) can overshoot when the cube is near the table edge, triggering the `MotionError` handler (line 51) and aborting the attempt.
- **Fix:** Reduce descent speed to `0.02` for the final centimetres, or add a `try/except` around the lift step to retry with a lower target height.