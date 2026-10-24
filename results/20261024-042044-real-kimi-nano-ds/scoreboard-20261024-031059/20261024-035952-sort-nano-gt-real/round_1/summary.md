**Mode 1 – Pick‑place collision (5 episodes)**
*Root cause:* The arm moves into the tray while lowering the cube, blocked by contact or joint limits (e.g., seed 1001 line 6.8, seed 1003 line 8.16).  
*Fix:* Raise the approach height in `place_into_tray` from 0.025 m to 0.04 m before lowering to 0.015 m, giving clearance over the tray rim.

**Mode 2 – Workspace over‑reach (1 episode)**
*Root cause:* `safe_move_to` called with x = 0.344 m outside the allowed [0.04, 0.32] m range; `MotionError` not caught (seed 1004).  
*Fix:* Clamp target coordinates to the workspace bounds before calling `robot.move_to`, or add `from math import pi` and define `MotionError` as `Exception`.

**Mode 3 – Gripper not releasing (2 episodes)**
*Root cause:* Cube retained in gripper because `place_into_tray` releases but the subsequent lift uses the old grip pose yaw, causing the arm to collide and drop the cube away from the tray (seed 1005, 1000).  
*Fix:* After releasing, call `safe_move_to(tx, ty, 0.05)` with no yaw, then re‑observe to get a fresh pose for the next pick.