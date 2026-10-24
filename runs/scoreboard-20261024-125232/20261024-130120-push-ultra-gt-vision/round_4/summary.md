**Mode 1: Reachability (4000, 4004)**  
*Episodes:* 2  
*Root cause:* `move_to` targets exceed the arm's 0.251 m wrist reach. Line 66 clamps start_x to 0.25, but push_dist (line 71) adds margin, pushing end_x beyond the workspace. The `except robot.MotionError` handler fails because `MotionError` does not exist in this SimRobot.  
*Fix:* Cap `push_dist` to `min(dist + NUDGE_DIST, 0.251 - puck_pos[0])` to keep end_x reachable. Replace `except robot.MotionError` with `except Exception` to catch the actual motion error.

**Mode 2: Puck not displaced (4001, 4005)**  
*Episodes:* 2  
*Root cause:* Pushes originate too close to the puck (line 66: `puck_radius + CLEARANCE`). With the puck too wide to grasp, the fingers collide with the table or puck sides, preventing forward motion despite successful `move_to` calls.  
*Fix:* Increase `CLEARANCE` from 0.06 to 0.12 on line 5 to push the start position farther back, ensuring fingertip clearance during the push trajectory.

**Mode 3: Tolerance miss (4003)**  
*Episodes:* 1  
*Root cause:* The final puck position (0.152, 0.014) is within 0.082 m of target but misses the 0.035 m radius. The nudge (line 99) adds only 0.01 m; with initial offset 0.082 m, the puck undershoots.  
*Fix:* Increase `NUDGE_DIST` from 0.01 to 0.03 on line 10 to provide sufficient corrective travel across attempts.