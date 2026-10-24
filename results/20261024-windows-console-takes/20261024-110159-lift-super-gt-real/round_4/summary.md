**Mode 1: Grasp slip (5 episodes)**
- **Root cause:** The lift after grasp uses `cz_after + 0.065` (line 63). With the cube at z≈0.015 m, target_z ≈ 0.08 m. The robot moves to this height but does not verify that the gripper is still closed; the subsequent `holding()` check (line 71) often returns false because the cube slides out during the move.
- **Fix:** After line 65, add a brief `robot.move_by(dz=0.01, speed=0.05)` to apply upward force, then re‑check `robot.holding()` before releasing.

**Mode 2: Approach/grasp miss (3 episodes)**
- **Root cause:** The approach height `grasp_z = cz + 0.02` (line 21) is only 2 cm above the cube. When the cube is at z≈0.015 m, `grasp_z` ≈ 0.035 m, leaving insufficient clearance for the robot’s hand geometry, causing the grasp to fail or slip immediately.
- **Fix:** Increase the offset to `cz + 0.04` (line 21) and raise `approach_z` accordingly (line 26), ensuring the robot reaches well above the cube before closing.

**Mode 3: Perception loss (1 episode)**
- **Root cause:** After a failed grasp the code retreats (`move_by(dz=0.02)`) but does not re‑observe before the retry (lines 44‑48). If the cube shifted, the second `attempt_grasp()` targets stale coordinates.
- **Fix:** Insert `obs = robot.observe()` after the retreat and before the retry, then extract fresh `cx, cy, cz`.