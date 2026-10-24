**Mode 1: Grasp failure (all episodes)**
- **Count:** 7/7
- **Root cause:** `robot.grasp()` returns `holding: null` at lines 65-67. The gripper closes but fails to acquire the cube, likely due to pose offset or slip.
- **Fix:** Increase `grasp_offset` from `0.08` to `0.12` (line 44) to approach from a higher, safer angle, or add a pre-grasp tap (move down 2mm, pause, then close).

**Mode 2: Verification offset exceedance (all episodes)**
- **Count:** 7/7
- **Root cause:** Cube released but lands outside the 4 cm tolerance (lines 106-110). The tray pose used for verification (line 80) is noisy; the cube lands slightly offset from the perceived tray centre.
- **Fix:** After release (line 89), move the robot to `lift_height` (line 93-94) then re‑observe the cube pose (add a `robot.get_pose(cube_name)` call) before the distance check, ensuring the check uses the actual final position rather than the stale tray pose.