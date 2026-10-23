**Mode 1: Systematic undershoot (6 episodes)**
*Root cause:* The push distance (0.04 m) is too short to overcome friction and reach the target radius. The robot stops short of the target every attempt.
*Code cite:* Line 7 (`push_distance = 0.04`) and lines 50–54 (push execution).
*Fix:* Increase `push_distance` to 0.08 m. This doubles the travel per attempt and should close the ~0.12 m gap within 2–3 tries.

**Mode 2: Approach blocked by contact (4 episodes)**
*Root cause:* The starting position (`approach_x/y`, lines 35–36) places the robot too close to the puck, causing immediate collision on `move_to`. The `back_offset` of 0.02 m is insufficient given the puck’s width.
*Code cite:* Lines 6–7 (`back_offset = 0.02`) and lines 35–44 (approach and collision handling).
*Fix:* Increase `back_offset` to 0.05 m. This gives the robot clearance to reach the push start pose without contacting the puck.

**Mode 3: Observation noise misaligns push direction (2 episodes)**
*Root cause:* Noisy `observe()` returns a puck position offset from true location, causing the unit vector (lines 31–32) to point slightly off-target. Repeated pushes drift the puck away from the circle.
*Code cite:* Lines 12–14 (observation) and 31–32 (direction calculation).
*Fix:* Apply a simple moving average to the puck position over the last 3 observations before computing `ux, uy`. This stabilizes the push direction at negligible compute cost.