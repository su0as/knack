**Mode 1 – Pre‑grasp collision (5 episodes)**
*Root cause:* The pre‑grasp pose (line 50) sits at `z = obj.z + 0.05 ≈ 0.065 m`, which is only 5 cm above the cube. The robot’s approach path or gripper geometry contacts the table or nearby objects before closure, causing the initial `grasp()` to return failure (lines 89‑93). The recovery nudge (line 97) lifts only 2 cm, still insufficient.
*Fix:* Raise `PRE_GRASP_Z` to `obj.z + 0.08` (8 cm offset) so the robot approaches from a safer height, giving fingers room to close without table contact.

**Mode 2 – Gripper slip/insufficient closure force (5 episodes)**
*Root cause:* After the first closure fails (line 89), the robot nudges upward by 2 cm (line 97) and retries. The subsequent `grasp()` still returns `holding: null`, indicating the gripper does not secure the cube. This suggests the gripper’s closing force or timing is inadequate for the cube’s weight/slip resistance.
*Fix:* Increase the nudge magnitude to `dz=0.04` (line 97) and/or add a brief `wait(0.2)` after the first closure to let fingers seat fully before the retry.