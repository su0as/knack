**Mode 1: Reach limit (40%)**
*Episodes: 3003, 3005, 3001, 3004*
*Root cause:* Start positions clamp to `0.04..0.32` (lines 53‑54) but target directions can push `start_x` beyond the arm’s `0.251 m` reach envelope. Line 69 `except MotionError` silently swallows the error, yet the arm physically cannot reach the clamped coordinate.
*Fix:* Reduce `start_x` upper bound to `0.25` to keep starts inside the reachable workspace.

**Mode 2: Short push (35%)**
*Episodes: 3000, 3002, 3006, 3007*
*Root cause:* `push_dist = dist + puck_radius + margin` (line 58) adds `puck_radius` to the travel distance. When `dist` is small (<0.15 m) the total distance exceeds the nudge range, stopping short of the target.
*Fix:* Cap `push_dist` at `dist + NUDGE_DIST` or remove `puck_radius` from the distance formula.

**Mode 3: Observation loss (15%)**
*Episodes: 3006, 3007*
*Root cause:* Intermittent `puck`/`target` missing from `observe()` (lines 23‑24), causing `get_poses()` to return `None` and the loop to break early.
*Fix:* Add a retry loop around `get_poses()` before proceeding with movement.