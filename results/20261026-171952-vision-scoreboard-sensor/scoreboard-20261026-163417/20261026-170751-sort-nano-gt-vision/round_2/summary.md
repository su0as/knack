**Mode 1: Tray pose unpack error (all 8 seeds)**  
- **Episodes:** 8/8  
- **Root cause:** `tray_info` values are stored as flat lists `[dx, dy]` (e.g., `red_cube_tray_dx`, `red_cube_tray_dy` in logs), but line 132 does `tray_x, tray_y = tray`, which expects a 2-tuple. The fixture parser returns a list, causing the `ValueError`.  
- **Fix:** Change line 132 to `tray_x, tray_y = tray[0], tray[1]` or ensure `tray_info` stores tuples.

**Mode 2: Approach blocked on red cube (seeds 2000, 2001, 2004–2005)**  
- **Episodes:** 5/8  
- **Root cause:** `robot.move_to` for the approach waypoint returns `{"ok": false}` because the gripper contacts the cube or workspace bounds before reaching `app_z`. The code then `continue`s, dropping the cube and retrying, but the same pose is reused, creating a loop.  
- **Fix:** Add a small vertical offset (e.g., `app_z += 0.01`) before the approach move, or log the blocked pose and adjust `FORWARD_OFFSET`/`SAFE_X_MAX` to avoid collision.