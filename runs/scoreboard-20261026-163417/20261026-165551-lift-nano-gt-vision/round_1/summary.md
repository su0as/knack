**Mode 1: Pre‑grasp too low (≈55 episodes)**
- **Root cause:** `pre_grasp.z = obj_pose.z + 0.02` (line 47) adds only 2 cm, but the cube centre is at ~0.015 m. The resulting pose sits at ~0.035 m, below the 5 cm lift requirement.
- **Fix:** Increase `offset` to `0.04` so `pre_grasp.z` ≈ 0.055 m, ensuring the subsequent lift starts above the target height.

**Mode 2: Grasp succeeds but lift stalls at ~0.05 m (≈45 episodes)**
- **Root cause:** `target_z = 0.05` (line 40) is exactly 5 cm; sensor noise and dynamics often leave the cube at 0.049 m (see check column). The `hold_pose` move_to lands just shy of the requirement.
- **Fix:** Raise `target_z` to `0.055` (5.5 cm) to provide a safety margin above the 5 cm threshold.

**Mode 3: Object slips during lift (≈15 episodes)**
- **Root cause:** No anti‑slip delay after `robot.grasp()` (line 106) before lifting; the gripper closes while the arm is still moving, causing the cube to slide out.
- **Fix:** Insert `robot.sleep(0.3)` immediately after the successful grasp (after line 112) before the lift move_to, allowing fingers to fully close.