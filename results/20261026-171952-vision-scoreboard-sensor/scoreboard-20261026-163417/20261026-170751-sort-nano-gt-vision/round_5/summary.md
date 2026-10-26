**Mode 1: Approach blocked / timeout (55 episodes)**
- **Root cause:** Repeated `move_to` failures due to collisions or joint limits; fallback loops exhaust the 70 s time budget (lines 56‑78, 185‑201).
- **Fix:** Increase `APPROACH_SPEED` from 0.05 to ~0.10 m/s to reduce contact time, and add a timeout guard inside `try_approach` to abort after N fallbacks instead of looping indefinitely.

**Mode 2: Cube lost / skipped (12 episodes)**
- **Root cause:** Visibility streak resets after 3 invisible frames (lines 90‑97) cause the blue cube to be skipped while the red cube succeeds (seed 5002, 5005).
- **Fix:** Raise the invisibility threshold from 3 to 5 frames, or reset `not_visible_streak` only when a new cube pose is detected.

**Mode 3: Grasp failure without retry (8 episodes)**
- **Root cause:** `grasp()` returns failure; code increments `grasp_retries` but then `continue`s, skipping the rest of the placement loop (lines 160‑171).
- **Fix:** After a grasp failure, `continue` should restart the outer `while` loop for that colour, not skip to the next colour iteration.