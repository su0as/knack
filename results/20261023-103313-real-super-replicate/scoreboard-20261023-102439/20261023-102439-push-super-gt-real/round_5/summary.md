**Mode 1: Motion blocked (5 episodes)**
*Root cause:* The `move_to` calls repeatedly fail with "stopped short of the target (blocked by contact or joint limit)" (e.g., seed 5000 lines 46–51). The robot cannot reach the calculated `approach_x/y` because the puck’s wide profile or the lateral corridor adjustment forces it into an unreachable pose.
*Fix:* Increase `back_offset` from 0.05 m to ~0.10 m (line 6) to start farther from the puck, or remove the lateral shortcut (lines 39–42) that shortens `push_distance` when `py` deviates from `ty`.

**Mode 2: Insufficient push distance (3 episodes)**
*Root cause:* After reaching the start pose, the puck does not travel far enough. In seed 5001 the final `puck_to_target_xy` is 0.11 m (line 68 check), exceeding the 0.035 m tolerance. The `push_distance` of 0.04 m (line 7) is too short for the observed initial offsets.
*Fix:* Raise `base_push_distance` from 0.04 m to 0.06 m (line 7) to give the puck more momentum per cycle.

**Mode 3: Observation noise / missed target (2 episodes)**
*Root cause:* The final check (line 68) shows `puck_to_target_xy` just above tolerance, suggesting the puck settles slightly off‑center despite `wait(0.2)` (line 65). Noise in `observe()` may misplace the perceived target position.
*Fix:* Extend the settle wait from 0.2 s to 0.5 s (line 65) or add a second `observe()` after `wait` before the final check (lines 68–73).