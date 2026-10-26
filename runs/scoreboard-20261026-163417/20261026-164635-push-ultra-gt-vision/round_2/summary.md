**Mode 1: Workspace boundary violation** (6 episodes)
*Root cause:* `push_distance` calculation (line 39) adds `2*puck_radius + 0.05` to the raw `dist`, pushing the target point outside the allowed x-range [0.04, 0.32] or y-range [-0.26, 0.26]. The `move_to` call at line 49 then triggers a safety halt.
*Fix:* Cap the push distance so the final target respects workspace limits. Clamp `push_x`/`push_y` to `[0.04+puck_radius, 0.32-puck_radius]` and `[-0.26, 0.26]` respectively before the move.

**Mode 2: Reachability failure** (1 episode)
*Root cause:* `push_distance` (line 39) produces a target at `0.319, 0.136` where the wrist point exceeds the arm’s 0.251 m reach (line 53). The code retries the same unreachable pose.
*Fix:* After computing `push_x, push_y`, verify the wrist point distance to base is ≤ 0.251 m. If not, reduce `push_distance` proportionally or choose a shallower push angle.

**Mode 3: Insufficient puck-to-target proximity** (3 episodes)
*Root cause:* The final distance check (line 79) uses `target_radius` (0.04 m) but episodes show `puck_to_target_xy` ≈ 0.05–0.09 m, exceeding tolerance. The approach/retract logic does not guarantee the puck stops inside the circle.
*Fix:* Increase the approach margin or add a post-push correction step that nudges the puck along the push vector until `final_dist ≤ target_radius`.