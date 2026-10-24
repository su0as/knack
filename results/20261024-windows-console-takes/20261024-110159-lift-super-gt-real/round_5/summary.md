**Mode 1 – Grasp never succeeds (6 episodes)**
- **Root cause:** `robot.grasp()` returns `False` every attempt (lines 38‑46). The arm descends, closes, but the gripper fails to close or the cube slips.
- **Fix:** Add a small retreat (`move_by(dz=0.02)`) after each failed grasp and re‑observe before the next try, as the code already intends. Ensure the approach pose (`approach_z = cz + 0.065`) gives enough vertical clearance for a reliable close.

**Mode 2 – Cube perceived too low (4 episodes)**
- **Root cause:** Perception reports `red_cube_z ≈ 0.015 m` (line 19), but the code’s `target_z = 0.0775 m` (line 54) assumes the cube centre is higher. The required height `0.065 m` cannot be met because the starting `cz` is underestimated.
- **Fix:** Increase the initial `grasp_z` offset (line 22) or add a perception correction step that raises `cz` if the observed `z` seems inconsistent with the workspace.

**Mode 3 – Motion error during lift (2 episodes)**
- **Root cause:** `robot.move_to(cx, cy, target_z, speed=0.1)` (line 56) throws `MotionError` when the arm cannot reach the commanded height, triggering `robot.release()` and failure (lines 58‑59).
- **Fix:** Reduce `speed` to `0.05` on the lift move, or add a `try/except` that attempts a lower `target_z` (e.g., `0.07`) before giving up.