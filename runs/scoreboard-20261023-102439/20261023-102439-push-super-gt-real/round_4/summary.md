**Mode 1: Systematic undershoot (6 episodes, seeds 4000‑4006)**
- **Root cause:** The approach point (`back_offset=0.02`) is too close to the puck. The robot stops short (`error_m≈0.012`) because the `move_to` collision detection triggers before reaching the intended push pose (lines 41‑46). The puck never receives enough impulse.
- **Fix:** Increase `back_offset` to `0.05 m` (line 6) to give the robot a clearer path and more push distance before contact.

**Mode 2: Wide lateral spread (seeds 4003‑4005)**
- **Root cause:** Large initial `y` offsets (e.g., puck at `y≈0.14`) cause the unit vector `uy` to dominate, steering the robot into side obstacles or joint limits, resulting in repeated short stops (lines 32‑33, 42).
- **Fix:** Add a lateral corridor check before `move_to`: if `|py‑ty| > 0.15`, reduce `push_distance` to `0.02 m` and retry, or nudge the approach point sideways (line 36‑37) to keep the trajectory centered.