**Mode 1 – Grasp failure (5 episodes)**
- **Root cause:** `grasp()` returns `holding: null` (line 67). The gripper cannot close on the cube, likely due to approach pose misalignment or insufficient downward force.
- **Fix:** Add a brief `robot.wait(0.05)` after `move_to` pre‑grasp (line 59) to let the robot settle, and verify `target_z` is exactly `PRE_GRASP_Z` (0.055 m) before closing.

**Mode 2 – Height insufficient after lift (3 episodes)**
- **Root cause:** Final `move_to` uses `LIFT_Z = 0.07 m` (line 83), but the perception step reports `red_cube_z ≈ 0.015 m`. The code never adds the cube’s base height (0.015 m) to the required clearance, so the robot lifts from a perceived base that is already on the table, ending ~5 cm short of the 0.065 m target.
- **Fix:** Change `LIFT_Z` to `REQUIRED_Z + cube_base_height` (0.065 + 0.015 = 0.080 m) or adjust the final `z` to `0.080` m (line 83).

**Mode 3 – Pre‑grasp pose out of reach (2 episodes)**
- **Root cause:** Horizontal offset `HOFFSET` (line 18) is applied unconditionally; when `cx` or `cy` are near zero the offset flips sign, pushing the target outside the robot’s workspace.
- **Fix:** Clamp the offset: `target_x = cx + max(-HOFFSET, min(HOFFSET, cx))` (lines 47‑48) to keep the pose within reachable bounds.