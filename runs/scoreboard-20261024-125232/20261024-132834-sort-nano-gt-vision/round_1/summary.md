**Mode 1: Approach collision (55%)**  
*Episodes:* 1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007  
*Root cause:* `move_to` to the tray target (line 65) stops short because the robot arm contacts the table or joint limits while descending from `place_target[2] += 0.005` (line 63). The 5 mm clearance is insufficient for the approach trajectory.  
*Fix:* Increase clearance to `+0.015` on line 63 and add a pre‑place `move_to` at `place_target[2] + 0.020` (line 65) to swing over the tray before descending.

**Mode 2: Grasp failure after placement (29%)**  
*Episodes:* 1000, 1003, 1004, 1005, 1007  
*Root cause:* `release()` (line 72) is called while the arm is still at tray height; the gripper may collide with the tray edge, causing the subsequent `grasp()` retries (lines 51‑52) to fail.  
*Fix:* After `release()` (line 72), execute `robot.move_to(place_target[0], place_target[1], place_target[2] + 0.020, speed=0.07)` (new line) before the `wait(0.3)` on line 73 to retract clear of the tray.