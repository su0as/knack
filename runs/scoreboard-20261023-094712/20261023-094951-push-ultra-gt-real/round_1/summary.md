**Mode 1: Safety violation (1 episode)**
*Root cause:* `start_xy` computed outside safe workspace [0.04, 0.32] (line 55). Puck near left edge causes negative x.
*Fix:* Clamp `start_xy` to workspace bounds before calling `move_to`.

**Mode 2: Stopped short by contact/joint limit (10 episodes)**
*Root cause:* `move_to` to `push_z` (line 56) fails when puck orientation blocks tool descent (upright puck presents edge-on profile). `approach_dist` (line 50) assumes clearance that isn't there.
*Fix:* Add a pre-touch check: if `puck["orientation"]` dot `push_dir` < 0.5, increase `approach_dist` by 0.02m or adjust `start_z` higher.

**Mode 3: Final distance > tolerance (5 episodes)**
*Root cause:* Push distance formula (line 62) adds `puck_radius + 0.02` but does not account for puck rotation during push. Upright pucks (seeds 1002, 1006, 1007) slide sideways, increasing lateral offset beyond the 0.035 tolerance.
*Fix:* Lead the push direction by `puck_radius` arc length: `push_dir = rotate_towards_target(to_target, puck_radius / dist_to_target)`.