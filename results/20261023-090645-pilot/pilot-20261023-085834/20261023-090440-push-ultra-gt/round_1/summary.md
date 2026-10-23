**Mode A: Overshoot / Slip** (3 episodes: 1003, 1007)
*Root cause:* The push length (`push_length = push_dist + 0.03`) is too short relative to the required stopping precision. The puck overshoots or slips past the target before the observation is taken.
*Fix:* Increase the push margin to `push_dist + 0.08` and add a brief reverse tap (`-0.02` m) at the end of the push trajectory to dampen overshoot.

**Mode B: Gripper collision / Misalignment** (1 episode: 1003)
*Root cause:* The gripper yaw is computed as `push_yaw + pi/2` (line 30). If the calculated start position places the gripper fingers into the puck or fixture, the robot may collide or fail to engage, resulting in `gripper holding None`.
*Fix:* Validate the start position clearance: ensure `start_x, start_y` are at least `puck_radius + 0.02` away from any obstacle before moving. If clearance is insufficient, shift the start position further back along the `-ux` axis.