**Mode 1: Overshoot & Collision (3 episodes: 4000, 4004, 4006)**
- **Root cause:** Push point clamped to workspace limits, then nudged `push_margin` larger (lines 63–67), driving the robot beyond reachable space. The puck was pushed off-target or collided.
- **Fix:** Cap `push_margin` at `puck_radius` before the nudge loop, preventing unbounded expansion.

**Mode 2: Approach/Retract Miss (2 episodes: 4000, 4004)**
- **Root cause:** After push, the robot retreated to `approach_x, approach_y` (lines 84–85), but the puck had already moved; the subsequent `observe()` missed the puck or logged stale positions.
- **Fix:** Move retraction to a fixed safe zone (e.g., `x=0.15, y=0`) independent of approach, then re-observe.

**Mode 3: Yaw Mismatch (1 episode: 4006)**
- **Root cause:** `push_yaw` computed from vector to target (line 70) misaligned with actual push direction after clamping, causing sideways slip.
- **Fix:** Recompute `push_yaw` from the clamped `push_x, push_y` vector just before the push call (line 78).