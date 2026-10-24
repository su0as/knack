**Mode 1: Overshoot & oscillation** (4 episodes: 5000, 5001, 5005, 5006)  
*Root cause:* Push distance formula `dist_xy * 1.1` (line 80) adds 10% buffer even when already close, causing the puck to travel past the target and bounce back.  
*Fix:* Cap push distance to `min(dist_xy, 0.15)` so short pushes dominate when near the target.

**Mode 2: Missed lateral alignment** (3 episodes: 5002, 5003, 5007)  
*Root cause:* Lateral shift `0.05 * sin(puck_yaw)` (line 46) is too small for yaw >10°, and the perpendicular offset (lines 47-48) uses `-dir_y`/`dir_x` which can point *away* from the target when the puck is yawed sideways.  
*Fix:* Increase lateral scaling to `0.15` and reverse sign to `+dir_y`/`-dir_x` so the push point slides *toward* the target axis.

**Mode 3: Descent blocks** (2 episodes: 5004 success, 5000/5001 retries)  
*Root cause:* Contact height drops to `base_contact_height` (0.03m) on flat pucks, causing finger collision (lines 50, 72).  
*Fix:* Raise nominal `base_contact_height` to `0.04` m to keep fingers clear of the table surface.