**Mode 1: Collision on tray approach** (5 episodes: 1000, 1001, 1002, 1004, 1005)  
*Root cause:* `move_to` above the tray stops short (lines 75–79) because the robot arm contacts the cube or tray edges before reaching `release_z=0.025`. The arm never descends to `release_above_table=0.015` (line 86), so the cube is not deposited.  
*Fix:* Lower the initial approach height to `0.020` before the final `0.015` descent, giving the arm clearance to navigate around the cube.

**Mode 2: Grasp failure on second cube** (4 episodes: 1003, 1006, 1007, plus partial 1000)  
*Root cause:* `grasp()` at lines 59/64 fails verification because the gripper approaches at `grasp_z=0.028` (line 53) without adjusting for object pose yaw. The subsequent retry at line 63 lifts only `0.01` m, insufficient to escape a collision.  
*Fix:* Increase retry lift to `0.025` m and ensure `move_to` uses `yaw=obj_pose["yaw"]` (line 54) for both initial and retry motions.

**Mode 3: Missing blue cube placement** (2 episodes: 1006, 1007)  
*Root cause:* After red cube placement, the blue cube grasp fails (Mode 2), so `continue` at line 67 skips the tray approach, leaving the blue cube on the table.  
*Fix:* Resolve Mode 2; blue cube will then be placed correctly.