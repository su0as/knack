**Mode 1: Grasp failure (7 episodes)**
- **Root cause:** `robot.grasp()` at line 71 closes the gripper, but the red cube never transitions to a held state. Verification at line 74 returns `False` because `robot.holding()` remains `None`.
- **Fix:** Inspect the gripper state before grasp. Ensure the approach pose (line 46) positions the gripper perpendicular to the cube face. Add a pre-grasp `robot.open()` at line 70 if fingers are closed.

**Mode 2: XY misalignment (5 episodes)**
- **Root cause:** The approach move (line 46) targets `tx, ty` derived from blue cube position (line 36). Observed red cube positions deviate laterally (xy_offset 0.06–0.20 m), indicating the red cube was not picked from its observed location.
- **Fix:** Before moving, verify `red_cube["pos"]` matches the detected `objects` centroid. If offset > 0.02 m, re-observe (line 11) or adjust `tx, ty` to the red cube’s actual coordinates rather than blue cube coordinates.

**Mode 3: Z‑gap / placement error (3 episodes)**
- **Root cause:** After lift (line 84) the cube is released at `lift_z` (line 81). Final positions show red cube z=0.015 m, barely above the blue cube (z_gap ≈ 0.0). The release may occur too low, causing the cube to rest on the table instead of stacking.
- **Fix:** Increase `lift_z` clearance to `tz + 0.05` (line 81) before release, ensuring the cube descends only after a safe height above the target.