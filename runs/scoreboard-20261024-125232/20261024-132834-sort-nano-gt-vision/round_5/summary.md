**Mode 1: Hold loss during descent** (4 episodes: 5000, 5001, 5003, 5005)  
*Root cause:* The robot releases the object at release height but the gripper opens or slips before the cube settles in the tray (lines 113–118). The `holding()` check after descent fails, triggering an abort.  
*Fix:* Add a brief `robot.wait(0.1)` after `robot.release()` (line 119) before the micro‑adjust nudge, allowing the cube to settle and the gripper to fully open before descent begins.

**Mode 2: Motion blocked by contact/joint limit** (3 episodes: 5002, 5004, 5005)  
*Root cause:* `safe_move` retries with reduced speed and lowered z, but the target pose still intersects a fixture or the table, causing repeated stops short (lines 31–59, specifically 54–56).  
*Fix:* Before the first `safe_move` in `pick_and_place` (line 72), shift the approach pose away from the tray edge by –0.02 m in x or y, ensuring the subsequent descent path is unobstructed.