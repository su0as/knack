**Mode 1: Insufficient lift height** (3 episodes: 2000, 2001, 2005)  
*Root cause:* The lift target `target_z = 0.0775` (line 49) is fixed, but the code never recomputes it from the actual cube height `cz`. When `cz` is low (e.g., 0.056 m), the robot stops at 0.0775 m, leaving the cube at ~0.056 m—below the 0.065 m requirement.  
*Fix:* After `observe()`, compute `target_z = cz + 0.065` (ensures centre ≥ 0.065 m) and use that in the final `move_to` (line 51).

**Mode 2: Grasp/descend collision** (2 episodes: 2001, 2005)  
*Root cause:* The approach/grasp Z values (lines 23, 33) are derived from `cz + 0.0125` and `cz + 0.025`. If the perceived `cz` is inaccurate or the cube sits on an uneven surface, the robot descends into the table or loses grip.  
*Fix:* Add a pre‑grasp height check: if `grasp_z < 0.03`, abort or raise `approach_z` by 0.01 m (line 23) to guarantee clearance.

**Mode 3: Gripper slip** (1 episode: 2001)  
*Root cause:* After a short retreat (line 42) the gripper releases (line 60) without re‑attempting.  
*Fix:* On grasp failure, retry the approach once before reporting failure.