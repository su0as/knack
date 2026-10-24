**Mode 1: Short stop on approach (55 episodes)**
*Root cause:* The `move_to` to `push_z` (line 53) or the push trajectory (line 61) encounters contact/joint limits before reaching the target z-height or push_end. The robot stops short, leaving the puck under-pushed.
*Fix:* Raise `push_start[2]` clearance on line 41 (e.g., `+0.15` instead of relying on `+0.1` on line 51) and increase `push_distance` on line 55 to `0.12` m to ensure full trajectory execution.

**Mode 2: Puck misses target laterally (30 episodes)**
*Root cause:* The offset behind the puck (line 36-41) uses `puck_radius + 0.015`. If the puck pose estimate has median error ~0.3 mm (observed), the push start offset error compounds, steering the puck off the direct line to the target.
*Fix:* Reduce the offset to `puck_radius + 0.005` on line 36 to minimise start-position error, and verify `target_info["radius"]` matches the green circle size (currently tolerance 0.035 m vs. puck radius 0.03 m).

**Mode 3: Retraction drag (15 episodes)**
*Root cause:* Retraction on lines 69-77 pulls the puck backward along the push direction (`- ux * 0.02`), potentially offsetting it away from the target before homing.
*Fix:* Change retraction to `push_end[0] + ux * 0.02` and `push_end[1] + uy * 0.02` to push the robot away from the puck, or set retract z to `push_end[2] + 0.05` to lift clear.