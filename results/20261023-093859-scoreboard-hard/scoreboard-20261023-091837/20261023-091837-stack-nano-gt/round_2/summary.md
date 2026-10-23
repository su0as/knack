**Mode 1: XY offset too large (seeds 2000, 2005, 2006, 2007)**
- **Episodes:** 4
- **Root cause:** The red cube’s XY position relative to blue is outside the placement tolerance. `find_object` may return a pose with significant pixel noise; the subsequent `move_to` places the gripper offset, so the release lands away from the blue cube’s center. Line 52 moves to the red pose directly, and line 85/93 use `red_yaw` but not a corrected XY target.
- **Fix:** After grasping, re‑observe the blue cube and compute a fresh target `(blue_x, blue_y, safe_z)` before lowering. This forces alignment at release (lines 83‑93).

**Mode 2: Release height missed (seeds 2005, 2007)**
- **Episodes:** 2
- **Root cause:** The release occurs at `place_center_z = blue_z + 0.03` (line 80), but the robot releases while still at the “safe height” `blue_z + 0.05` (line 83) or the subsequent `move_to` to `place_center_z` overshoots/undershoots due to noise. The log shows `got 0.0186, expected 0.0434` (seed 2007, line 125).
- **Fix:** Ensure the final `move_to` targets `blue_z + 0.03` *after* the safe‑height move, and verify `holding()` is still true immediately before `release()` (line 100‑103).