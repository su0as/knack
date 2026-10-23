**Mode 1: Off-target placement** (3 episodes: 1001, 1005, 1006)
*Root cause:* The robot moves to the tray’s nominal position, but the cube is released at a tray coordinate offset from the cube’s original location. The check `yellow_cube_tray_dx/dy` exceeds 0.02m.
*Fix:* After `robot.move_to(tx, ty, place_z)`, add a final `robot.move_to(cx, cy, place_z)` to align the cube over its original grid cell before release.

**Mode 2: Short stroke to placement height** (1 episode: 1002)
*Root cause:* `robot.move_to(tx, ty, place_z)` stops short (error 0.0117m) due to contact or joint limit at line 56.
*Fix:* Increase `place_z` by 0.01m (e.g., `tz + 0.025`) to clear any tray edge or fixture collision.

**Mode 3: Premature release** (1 episode: 1005)
*Root cause:* `robot.release()` at line 62 executes while the arm is still over the pickup pose (x≈0.136, y≈0.0), not the tray. The cube lands near the start location.
*Fix:* Ensure the arm traverses the full transfer path (above tray → placement height) before calling `release()`.