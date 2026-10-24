**Mode 1: Reach overflow** (5 episodes: 5002, 5003, 5004, 5006, 5007)
*Root cause:* `push_dist` computation at line 71 adds `NUDGE_DIST` to `dist`, but clamps to `REACH_LIMIT - puck_pos[0]`. When the puck is near the workspace boundary, `push_dist` becomes negative or zero, triggering the fallback at line 73 (`min(dist + NUDGE_DIST, 0.05)`), which still exceeds reach. The arm then throws `MotionError` (traces confirm).
*Fix:* Cap `push_dist` at `REACH_LIMIT - puck_pos[0] - 0.01` to guarantee a safety margin, and ensure the fallback never exceeds this margin.

**Mode 2: Insufficient push distance** (5 episodes: 5000, 5001, 5005)
*Root cause:* The push travels `dist + NUDGE_DIST` (line 71), but `NUDGE_DIST = 0.03` is too small to overcome friction or compensate for pose latency. Episodes end with `puck_to_target_xy` ≈ 0.2–0.27 m, well above the 0.035 tolerance.
*Fix:* Increase `NUDGE_DIST` to 0.08–0.10 m. This extends the push range without altering reach logic.

**Mode 3: Observation/pose staleness** (2 episodes: 5002, 5003)
*Root cause:* `get_poses()` returns stale data; the arm moves to a position based on outdated puck location, causing misses. Low camera frame counts (6/6 or 7/7) suggest tracking loss.
*Fix:* Add a `robot.wait(0.1)` after `observe()` in `get_poses()` to ensure fresh data, and log a warning if `puck_radius` changes > 0.02 between retries.