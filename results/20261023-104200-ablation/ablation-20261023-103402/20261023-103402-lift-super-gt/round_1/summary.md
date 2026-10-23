**Mode 1: Insufficient lift height** (5 episodes: 1000, 1002, 1003, 1004, 1007)  
*Root cause:* The lift height `lift_z = cz + 0.07` (line 19) places the gripper at ~8.5 cm above the table, but the final observed cube z‑coordinate is consistently ~0.064 m (6.4 cm). The cube is not rising enough, likely because the grasp opening is too large or the lift speed is insufficient.  
*Fix:* Increase `lift_z` to `cz + 0.10` (10 cm above centre → ~11 cm above table) and add a post‑lift check that `gripper_z >= 0.07` before the verification step (line 47).

**Mode 2: Grasp failure / drop** (3 episodes: 1001, 1005, 1006)  
*Root cause:* The initial grasp succeeds but the cube is left at table height (z≈0.015 m). The `grasp()` call at line 30 may close on an unstable pose, and `release()` on line 32 (retry logic) is never triggered because the code proceeds to lift without confirming a secure hold.  
*Fix:* After `grasp()` (line 30), insert `if not robot.holding() == "red_cube": return False` before the lift move (line 39). This aborts early if the gripper did not secure the cube.