**Mode 1 – Pre‑grasp unreachable (5 episodes)**
*Root cause:* The pre‑grasp pose `PRE_GRASP_Z = obj.z + 0.08` yields ~0.095 m, but the robot moves to z ≈ 0.093 m (line 58) and the cube sits at z=0.015 m. The gripper closes at this height, colliding with the table before fingers can close (lines 91‑92).
*Fix:* Raise `PRE_GRASP_Z` to `obj.z + 0.12` (line 40) to give clearance above the table surface.

**Mode 2 – Grasp closure failure (12 episodes)**
*Root cause:* All attempts close the gripper at ~0.09 m (lines 91, 100). With the cube at z=0.015 m and the robot at 0.09 m, the fingers hit the table, returning `holding: null` (traces show `opening: 0.0`).
*Fix:* Add a nudge `robot.move_by(dz=0.04)` (line 99) *before* the first `grasp()` call, or increase `PRE_GRASP_Z` as in Mode 1 to ensure the gripper starts above the table.