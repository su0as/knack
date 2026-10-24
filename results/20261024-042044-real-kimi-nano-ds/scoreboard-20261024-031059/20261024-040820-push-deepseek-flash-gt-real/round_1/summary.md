**Mode 1: Out-of-reach push point** (2 episodes: 1000, 1001)  
*Root cause:* The `clamp` on line 31 forces `cx` to 0.31 when the puck is far right, but the arm’s max reach is 0.251 m (wrist). Line 30’s `margin = r + 0.012` adds extra distance, pushing the target beyond the workspace.  
*Fix:* Reduce the margin or lower the `cx` clamp ceiling (e.g., `0.25`) to keep the approach point inside the arm’s envelope.

**Mode 2: Timeout on vertical descent** (2 episodes: 1003, 1007)  
*Root cause:* Line 55 moves to `z=0.02` at slow speed (0.05) to set push height. When the puck is near the target, this tiny descent takes many waypoints, exhausting the 45 s budget before the push executes.  
*Fix:* Increase the descent speed to `0.15` on line 55, or raise the target `z` to `0.05` to reduce waypoint count.

**Mode 3: Gripper collision / puck tilt** (1 episode: 1002)  
*Root cause:* Line 76 lifts the gripper from `z=0.02` after the push. The puck’s edge may catch the jaw geometry during retreat, causing a stall that the code does not recover from, leaving the puck off‑center.  
*Fix:* Add a small `yaw` offset or a brief `open` command on line 76 to ensure the jaws clear the puck before lifting.