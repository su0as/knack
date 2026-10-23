**Mode 1: Systematic short-stops (5 episodes: 1000, 1002, 1003, 1006, 1007)**
*Root cause:* The `robot.move_to` calls repeatedly halt early with `"stopped short of the target (blocked by contact or joint limit)"`. The code treats this as a transient error and retries from the same approach vector, never adjusting aim.
*Fix:* After a short-stop, recompute the unit vector `ux, uy` from the *new* observed puck position before the next `move_to` (lines 31‑32). This steers around the obstacle rather than replaying a blocked trajectory.

**Mode 2: Overshoot / loss of puck (2 episodes: 1003, 1006)**
*Root cause:* After a successful `move_to`, the puck shifts during `wait(0.2)` or subsequent observation, but the code uses the *initial* `px, py` for the final check (lines 59‑65). In seed 1006 the puck ends outside the circle despite earlier success.
*Fix:* Re-read `puck['pos']` immediately before the final distance check (line 61) rather than relying on stale variables from earlier iterations.