**Mode 1: Systematic short-stops** (seeds 3000, 3003, 3004, 3005, 3007)
- **Count:** 5 episodes
- **Root cause:** The `move_to` calls repeatedly report `"stopped short of the target (blocked by contact or joint limit)"`. The robot cannot reach the computed `approach_x/y` or `push_x/y` poses, likely because the `back_offset=0.05m` positions the tool into the puck or a fixture, or the `push_distance=0.08m` overshoots a physical stop.
- **Fix:** Reduce `back_offset` to `0.02m` (line 7) and/or reduce `push_distance` to `0.04m` (line 8) to keep motions within reachable space.

**Mode 2: Overshoot / missed target** (seeds 3001, 3002, 3006)
- **Count:** 3 episodes
- **Root cause:** Successful motions still leave `puck_to_target_xy` near the tolerance boundary (0.023–0.048m). The push distance may be too large or direction slightly off, failing to guarantee entry on every attempt.
- **Fix:** Add a final micro-push after the loop (after line 75) that moves `push_distance/2` toward the target if `dist_to_target > 0.02m`, using the smoothed puck position from the last observation.