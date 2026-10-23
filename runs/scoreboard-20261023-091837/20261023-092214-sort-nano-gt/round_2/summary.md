**Mode 1: Missed grasp (all 8 seeds)**
- **Count:** 8/8
- **Root cause:** Grasp verification fails at line 68 (`robot.holding() != obj_name`). The robot releases the cube before it is securely held, or the gripper slips on the smooth cube surface.
- **Fix:** Increase the initial grasp height (line 56) by 0.005 m and add a post-grasp lift check at line 72 before release.

**Mode 2: Tray placement offset (all 8 seeds)**
- **Count:** 8/8
- **Root cause:** After a successful grasp, the robot moves to the tray release height (line 87) but descends to 0.015 m (line 98) without correcting for tray‑center alignment. Small approach errors accumulate, placing the cube off‑center (dx/dy > 0.05 m).
- **Fix:** Before release (line 98), add a final `robot.move_to(tray_x, tray_y, 0.020, speed=0.05)` to centre the cube over the tray, then lower to 0.015 m.