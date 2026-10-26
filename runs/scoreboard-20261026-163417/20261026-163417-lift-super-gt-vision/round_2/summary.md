**Mode 1: Z-clearance shortfall (62 episodes)**
- **Root cause:** `move_to_pose` descends to `GRASP_Z = 0.015` (line 56, 69). After grasping, the lift target uses `SAFE_Z = 0.065` (line 85), but the final pose settles at `0.064`–`0.065` due to numerical drift or motor quantization, falling below the 5 cm requirement.
- **Fix:** Add a post‑lift verification step: after the lift move (line 86), check `robot.holding()["pos"][2]`. If `< 0.065`, execute a tiny `robot.move_by(dz=0.002, speed=0.05)` to guarantee clearance.

**Mode 2: Grasp failure (12 episodes)**
- **Root cause:** The approach/descend moves succeed (lines 64, 69), but `robot.grasp()` (line 74) does not secure the cube, triggering the retreat/release fallback (lines 79–81) and early termination.
- **Fix:** Before descending, ensure the approach pose is exactly `SAFE_Z` (line 61) and that `cube_info["pos"][2]` matches `GRASP_Z`. If the cube height estimate is off, adjust `grasp_pos[2]` by `+0.001` m before the descend call (line 69).