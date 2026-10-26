**Mode 1: Overshoot / undershoot (2 episodes: 2002, 2003)**
*Root cause:* The push distance uses `dist_to_target + OVERSHOOT`, but `OVERSHOOT=0.005` is too small relative to the 0.035 tolerance. In seed 2002 the puck stopped at 0.045; in 2003 it stopped at 0.034 (just outside).
*Fix:* Increase `OVERSHOOT` to `0.020` (line 9) to guarantee crossing the tolerance boundary.

**Mode 2: Position clamp collision (2 episodes: 2003, 2004)**
*Root cause:* Start point clamping (lines 57-58) pushes the robot into a corner where the puck cannot be reached cleanly, causing erratic motion. Seed 2003 ends upright=False, indicating a tilt from a poor approach angle.
*Fix:* Widen the workspace bounds to `start_x: max(0.02, min(0.34, ...))` and `start_y: max(-0.28, min(0.28, ...))` to keep start points away from edges.

**Mode 3: Observation loss / perception dropout (2 episodes: 2004, 2005)**
*Root cause:* After the push, `obs2` sometimes loses the puck (lines 93-96), likely because the robot retreats into a blind spot or the puck rolls out of view. This prevents the verification loop from confirming success.
*Fix:* Add a retreat buffer: after the final `move_to(end_x, end_y, APPROACH_Z)`, insert a small backward shift `robot.move_to(end_x, end_y - 0.02, APPROACH_Z)` before the second observe to keep the puck in camera frame.