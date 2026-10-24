**Mode 1 – Tray‑approach collision (seeds 4001, 4005, 4007)**  
*Episodes:* 3  
*Root cause:* After releasing the red cube, the planner moves to the blue‑tray centre without re‑checking joint limits. In 4001 the move `move_to(0.058, 0.123, 0.025, yaw=0.467, speed=0.070)` (line 10.68) is blocked by the red cube still in the workspace. In 4005 and 4007 the approach vectors cross the red‑cube position, causing a contact stop before reaching the tray.  
*Fix:* Insert a `safe_move_to` with a high clearance `z=0.06` between tray placements (after line 141) to fly over the just‑placed cube before heading to the next tray.

**Mode 2 – Grasp failure on blue cube (seeds 4005, 4006)**  
*Episodes:* 2  
*Root cause:* The blue‑cube pose is near the workspace edge `SAFE_Y=(−0.26, 0.26)`. In 4005 the approach `move_to(0.089, -0.180, 0.025, yaw=0.205)` (line 10.48) undershoots the safety bounds, triggering a MotionError. In 4006 the initial pick `move_to(0.090, 0.169, 0.025, yaw=−0.752)` (line 4.7) exceeds `SAFE_X` limit, causing an immediate halt.  
*Fix:* Clamp the blue‑cube `y` coordinate with `clamp_coord(y, SAFE_Y)` before the pre‑grasp move (line 38) and enforce `x` clamping at line 37 to keep all pick poses inside the safety box.