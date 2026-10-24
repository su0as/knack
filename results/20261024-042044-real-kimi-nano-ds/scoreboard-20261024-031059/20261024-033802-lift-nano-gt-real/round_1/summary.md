**Mode 1 – Grasp failure (6 episodes)**  
*Root cause:* `robot.grasp()` returns `False` every attempt (lines 65‑69). The gripper does not close or slips.  
*Fix:* Increase approach speed to `0.10` and add a pre‑grasp `move_to` with `z=0.05` to seat the fingers, then retry.

**Mode 2 – Motion unreachable (4 episodes)**  
*Root cause:* `move_to` reports `ok: true` but the robot stops short (z≈0.065, final cube z=0.015). The target height is unreachable from the starting pose (lines 50‑62).  
*Fix:* Reduce `LIFT_Z` to `0.055` and add a `wait(0.1)` after `move_to` before `grasp` to allow settling.

**Mode 3 – Perception lag (1 episode)**  
*Root cause:* Cube reported at z=0.015 while code expects lift above 0.065; the observation is stale (line 21).  
*Fix:* Insert `robot.wait(0.5)` after `observe()` to ensure fresh pose before computing `target_z`.