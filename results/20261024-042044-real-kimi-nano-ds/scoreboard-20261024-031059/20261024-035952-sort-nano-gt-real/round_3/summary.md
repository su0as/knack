**Mode 1 – Missed grasp (3002, 3006, 3007)**
- **Episodes:** 3
- **Root cause:** Grasp opens without holding the cube (lines 80‑85). The robot attempts to close fingers but the gripper either slips or the object is not properly presented, causing `holding()` to return `null` immediately after `grasp()`. Subsequent placement fails because nothing is held.
- **Fix:** Add a verification lift after `grasp()` (insert `safe_move_to(ox, oy, 0.04, yaw=oyaw, speed=0.07)` before the `holding()` check at line 88) to ensure the cube is securely lifted before release.

**Mode 2 – Tray placement off‑target (3001, 3004)**
- **Episodes:** 2
- **Root cause:** `place_into_tray` uses the tray pose from `get_pose` (line 112) but the tray may have shifted or the approach vector is misaligned with the tray centre, causing the cube to land outside the tray boundaries (large `dx/dy` errors).
- **Fix:** After releasing (line 128), execute a micro‑adjust: `safe_move_to(tx, ty, release_z + 0.005, speed=0.03)` to nudge the cube into the tray before the final lift.