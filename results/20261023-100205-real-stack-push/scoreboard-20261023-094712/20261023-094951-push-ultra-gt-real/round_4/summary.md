**Mode 1: Start-position collisions (30%)**
- **Episodes:** 4003, 4005, 4006
- **Root cause:** `start_xy` computed via `clamp_xy` (line 68) can land the robot against workspace walls or puck, triggering joint limits. The `clamp_xy` function (lines 9–10) silently snaps coordinates, removing clearance needed for safe approach.
- **Fix:** Before clamping, verify `start_xy` keeps at least 0.05 m clearance from `X_MIN/X_MAX/Y_MIN/Y_MAX`. If violated, shift `push_dir` opposite the nearest wall before recomputing `start_xy`.

**Mode 2: Push moves stopped short by contact (55%)**
- **Episodes:** 4000, 4001, 4002, 4004
- **Root cause:** `robot.move_to(end_xy[…], local_push_z, yaw=push_yaw, speed=0.05)` (line 86) attempts high-speed (0.05) Cartesian motion while pushing. The puck jams against the target fixture or robot base, and the motion controller aborts early to protect hardware.
- **Fix:** Reduce push speed to `0.02` on line 86. Add a pre-push check: if `dist_to_target < 0.1`, set `approach_dist = 0.08` to start farther back, reducing initial contact force.