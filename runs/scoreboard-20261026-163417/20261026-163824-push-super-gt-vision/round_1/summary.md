**Mode 1: Overshoot / blocked motion** (1 episode: seed 1007)
*Root cause:* The push distance `dist_to_target + OVERSHOOT` (line 60-61) combined with workspace clamping (lines 57-58, 62-63) can push the robot into a joint limit or contact, causing `move_to` to stop short (trace t=7.94). The robot retracts without reaching `end_x, end_y`, leaving the puck short of the target.
*Fix:* Reduce `OVERSHOOT` from `0.02` to `0.005` so the end point stays well within limits, or add a post-push nudge if `final_dist` is just above the radius.

**Mode 2: Perception / observation loss** (0 episodes in given data, but possible)
*Root cause:* If `observe()` fails or puck is lost (lines 93-96), the episode retries without correcting aim.
*Fix:* After a failed observe, log the last known puck pose and aim a corrective push toward the target before retrying, rather than blindly `continue`.