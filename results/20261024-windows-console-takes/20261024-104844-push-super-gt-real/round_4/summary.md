**Mode 1: Lift collision on approach (3 episodes: 4000, 4001, 4007)**
*Root cause:* The robot lowers to `contact_height` (line 72) before confirming the path is clear. When the puck is near the target edge, the lowered gripper contacts the table or fixture, triggering the `except` at line 73–76 and retreating without pushing.
*Fix:* Add a pre-lift-check: before line 71, test `robot.move_to(behind_x, behind_y, lift_height, speed=travel_speed)`. If it fails, skip this attempt rather than lowering into an obstacle.

**Mode 2: Short stop due to contact/joint limit (3 episodes: 4000, 4001, 4007)**
*Root cause:* After successfully reaching `lift_height`, the subsequent `move_to` to `contact_height` (line 72) is reported as `ok: false` with "stopped short". This indicates the robot cannot physically reach the low height from its current pose, likely due to singularity or workspace limits.
*Fix:* Increase `contact_height` baseline (line 14) from `0.02` to `0.03`. This raises the contact point, keeping the robot in a safer pose while still allowing effective pushing.