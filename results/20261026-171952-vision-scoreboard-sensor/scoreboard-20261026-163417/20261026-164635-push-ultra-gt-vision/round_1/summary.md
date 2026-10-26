**Mode 1: Overshoot / Under-push (5 episodes)**
*Root cause:* `push_distance` (line 38) adds `puck_radius + 0.02` to `dist`, but the push stops at the calculated `push_x/push_y`. The puck does not travel far enough to overcome inertia and settle inside the circle.
*Fix:* Increase `push_distance` margin. Change line 38 to `push_distance = dist + 2 * puck_radius + 0.05` to ensure the robot pushes well beyond the target before retracting.

**Mode 2: Yaw misalignment (2 episodes, seeds 1006/1007)**
*Root cause:* `push_yaw` (line 44) adds `pi/2` to `atan2(uy, ux)`. If the robot's end-effector orientation convention differs from the simulation, the puck slides sideways instead of forward.
*Fix:* Verify yaw convention. If pushing forward results in lateral slip, remove the `+ math.pi/2` offset on line 44, or invert the sign to `- math.pi/2`.

**Mode 3: Approach offset (1 episode, seed 1004)**
*Root cause:* `approach_dist` (line 32) uses `2 * puck_radius + 0.03`. The puck is "too wide to grasp," so the approach point may be too close, causing the robot to collide or push at a suboptimal angle.
*Fix:* Increase `approach_dist`. Change line 32 to `approach_dist = 3 * puck_radius + 0.05` to ensure a safer, clearer push trajectory.