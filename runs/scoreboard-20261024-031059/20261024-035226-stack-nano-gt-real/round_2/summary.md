**Mode 1: Grasp failure (5 episodes: 2000, 2002, 2003, 2005, 2007)**
*Root cause:* The gripper closes but `holding()` check fails (lines 45‑49). Often the cube slips or the initial `move_to` (line 38) undershoots, preventing a secure seat.
*Fix:* Add a pre‑grasp touch test or increase `pick_z` clearance by +0.01 m, and log the `error_m` from `move_to` to detect joint limits early.

**Mode 2: Placement xy‑offset too large (4 episodes: 2001, 2003, 2005, 2007)**
*Root cause:* After lifting, the perceived red‑cube position drifts >0.02 m from the blue cube target (lines 80‑104). The placement move (line 63) succeeds but the offset check aborts the attempt.
*Fix:* Before the placement move, run a quick “hover‑and‑check” at `place_z‑0.01` to verify xy alignment; if offset >0.015 m, adjust the gripper x/y by the measured drift before committing.

**Mode 3: Move‑to collision/limit short‑stop (2 episodes: 2004, 2005)**
*Root cause:* `move_to` returns `ok:false` with note “stopped short” (lines 40, 65). The arm hits a joint limit or the cube stack.
*Fix:* Catch the `ok:false` response and immediately `robot.log` the `pos` and `error_m`; then back‑off `dz=-0.02` (line 92) or shift the target x/y by ±0.02 m before retrying.