**Mode 1: Overshoot & drop** (3 episodes: 1001, 1005, 1004)
*Root cause:* The push distance (`push_distance = dist_xy + approach_offset`) is too large for the contact speed, causing the puck to slide past the target or lose grip before centering. Line 54 adds `approach_offset` to the remaining distance, which compounds when the puck is already close.
*Fix:* Cap `push_distance` to `max(dist_xy, approach_offset)` so the gripper only pushes the remaining gap, not the full separation plus offset.

**Mode 2: Upright failure / tilt** (2 episodes: 1002, 1005)
*Root cause:* The puck is pushed while the gripper is still in contact, but no correction for rotational momentum is applied. If the approach angle is slightly off, the puck tips. Lines 35–36 compute `behind` point without checking puck orientation; lines 57–59 move the gripper linearly, ignoring tilt.
*Fix:* Add a pre-push check: if `puck["orientation"]` deviates >10° from vertical, adjust `behind_x/behind_y` laterally by `0.02m` to push straighter, or lift slightly higher (`contact_height + 0.01`) to reduce friction torque.

**Mode 3: Reach/visibility failure** (2 episodes: 1002, 1004)
*Root cause:* The robot attempts `move_to` to poses that are perceptually blocked or outside the workspace after the initial approach, triggering the `except` handler at line 41/48 and resetting pose without progress.
*Fix:* Before lowering to `contact_height`, verify `dist_xy > 0.05m`; if closer, skip the push and only reposition laterally using `travel_speed` before retrying the push loop.