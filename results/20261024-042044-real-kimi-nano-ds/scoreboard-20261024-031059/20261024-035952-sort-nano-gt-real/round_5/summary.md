**Mode A – Tray‑pose read failure (5000, 5001, 5002, 5004, 5005, 5007)**  
*Episodes:* 6  
*Root cause:* `place_into_tray` calls `robot.get_pose(tray_name)` (line 119) but the returned pose is sometimes stale or mis‑aligned with the cube’s actual location, causing the arm to aim off‑centre.  
*Fix:* After `get_pose`, add a short `robot.wait(0.05)` and re‑read the pose before lowering; or use the cube’s last known `ox, oy` from `pick` as the tray target instead of a fresh pose read.

**Mode B – Grasp failure on blue cube (5000, 5005, 5007)**  
*Episodes:* 3  
*Root cause:* The blue cube sits near workspace edges; `pick` clamps coordinates (lines 66‑68) but the resulting pose still falls outside the reachable envelope, triggering `MotionError` and an early release.  
*Fix:* Expand `SAFE_X`/`SAFE_Y` margins by ~0.02 m, or add a pre‑grasp check: if `abs(ox‑0.15) > 0.12` or `abs(oy) > 0.18`, abort and retry with a shifted approach pose.

**Mode C – Contact/joint limit stop (5005)**  
*Episodes:* 1  
*Root cause:* `move_to` to the blue‑tray approach (line 142) stopped short due to contact detection (error_m 0.0134, note “blocked by contact or joint limit”).  
*Fix:* Raise the approach `z` from 0.045 m to 0.055 m for the blue tray, or insert a `robot.wait(0.02)` after the move to let dynamics settle before release.