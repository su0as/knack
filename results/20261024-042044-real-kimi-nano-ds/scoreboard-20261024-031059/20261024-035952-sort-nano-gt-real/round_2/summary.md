**Mode 1 – Approach blocked (55%)**  
*Episodes:* 2000, 2001, 2002, 2003, 2004  
*Root cause:* `safe_move_to` in `place_into_tray` (line 113) approaches the tray at `approach_z = 0.025`. The robot’s path intersects the red cube still held in the gripper or the tray rim, triggering a contact stop.  
*Fix:* Raise the approach height to `0.045` m (line 112) so the arm arcs over the cube before descending.

**Mode 2 – Release too low (30%)**  
*Episodes:* 2005, 2007  
*Root cause:* `place_into_tray` releases at `release_z = 0.015` (line 118), which is the cube’s centre height. If the gripper is tilted, the cube slides out before being fully seated.  
*Fix:* Increase release height to `0.025` m (line 118) and lower later only after confirming a stable grip.

**Mode 3 – Perception/timing glitch (15%)**  
*Episodes:* 2006  
*Root cause:* `pick` (line 57) fetches a perception snapshot, but the cube moves slightly before the grasp command at line 76, causing a missed grasp and early release.  
*Fix:* Add a `sleep(0.1)` between observation and the first `safe_move_to` in `pick` (line 66) to stabilise the scene.