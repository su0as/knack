**Mode 1: Missed grasp (all 7 seeds)**  
*Episodes:* 7  
*Root cause:* The robot lifts to `grasp_z + 0.025` (line 70) but the object remains unheld. The subsequent lift (line 81) adds only `0.01 m`, insufficient to secure the grip before transport.  
*Fix:* Increase the retry lift to `grasp_z + 0.040` and the post‑grasp lift to `grasp_z + 0.030` to ensure the cube is firmly held before moving.

**Mode 2: Tray‑approach offset (all 7 seeds)**  
*Episodes:* 7  
*Root cause:* Final release positions show cubes landing `dx/dy ≈ 0.05–0.13 m` from tray centres (check columns). The centering move at line 107 uses the same target as line 98 without correcting prior drift, so the robot releases off‑centre.  
*Fix:* Add a corrective `move_to` after line 107 that targets the exact tray centre `(tray_x, tray_y, 0.020)` at `speed=0.05` before the release descent at line 117.