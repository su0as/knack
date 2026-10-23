**Mode 1: Premature release (5 episodes)**
- **Root cause:** `release()` at line 123 fires while the gripper is still translating horizontally. The code moves to `red_top_z` (line 58) then immediately computes a horizontal offset using `get_pose('red_cube')` (line 68). The pose update lags; the robot releases before reaching the target x/y, dropping the cube at the start position.
- **Fix:** Insert `robot.move_by(dx, dy, speed=0.15)` (line 74) *before* `release()`, ensuring horizontal arrival is confirmed.

**Mode 2: Stack height overflow (3 episodes)**
- **Root cause:** `target_z_tool` (line 97) computes `blue_z + 1.5*h_red + ...`. With `h_red ≈ 0.05` and `blue_z ≈ 0.015`, the result ≈ 0.092 m, but `MAX_Z = 0.245` clips it. However, the subsequent `move_to` (line 113) targets the capped height, yet the gripper is already offset from the blue cube centre, causing a miss.
- **Fix:** After horizontal move (line 74), re-observe blue pose and recompute `target_z_tool` using the actual `blue_pose` before the final `move_to` (line 113).

**Mode 3: XY offset drift (2 episodes)**
- **Root cause:** Horizontal move (line 74) uses `dx, dy` computed from `red_current` (line 68-70). If `red_current` is stale or the robot’s base pose shifts, the offset misaligns with the blue cube. The released cube lands offset (xy_offset ~0.04 m).
- **Fix:** After `grasp_cube`, re-query `obs2` (line 51) for fresh red pose before computing `dx, dy`, ensuring the horizontal move targets the current red position.