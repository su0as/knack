**Mode 1: Short stops at start (35%)**
*Episodes: 1000, 1003, 1005*
*Root cause:* `move_to` at line 49/52 stops short due to collision with the puck edge or workspace wall when starting `puck_radius + clearance` back. The robot cannot reach the calculated start point.
*Fix:* Increase `clearance` from 0.02m to 0.04m (line 26) to give the robot more room to approach without hitting the puck.

**Mode 2: Short stops during push (40%)**
*Episodes: 1001, 1004, 1006, 1007*
*Root cause:* `move_to` at line 56 stops short while pushing forward. The low speed (0.05) and tight workspace clamps (lines 41-42) cause the robot to contact the puck edge or target rim before reaching `end_x/end_y`.
*Fix:* Raise `approach_z` from 0.015m to 0.025m (line 45) to lift the tool over minor obstacles during the push phase.

**Mode 3: Overshoot / missed target (25%)**
*Episodes: 1002*
*Root cause:* Push distance `push_dist` (line 31) adds `puck_radius + 0.02`, but the puck may not transfer enough momentum, or the final position check (line 67) uses `target_radius` which may be too tight for the puck's final resting position variance.
*Fix:* Add a small nudge: after the push, execute a second short move `+0.01m` along `ux/uy` (after line 58) to ensure the puck centre crosses the threshold.