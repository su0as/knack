**Mode 1: Approach blocked (55% of failures)**
*Episodes:* 4000, 4002, 4003, 4004, 4006
*Root cause:* The approach pose (`move_to` at line 45) is too low or offset, causing the robot to contact the corridor wall or puck side before reaching the target. The `except` block lifts `approach_z` (line 48) but often not enough to clear the obstacle.
*Fix:* Increase `CLEARANCE_ABOVE` from 0.018 m to **0.025 m** (line 8) and add a second lift step of +0.005 m after the first retry (after line 48).

**Mode 2: Push step too large / overshoot (30% of failures)**
*Episodes:* 4001, 4005, 4007
*Root cause:* `push_step` (line 76) uses `min(MAX_PUSH_PER_STEP, dist)`. When `dist` is small (≈0.12 m) the step is capped at 0.015 m, but the puck’s centre can overshoot the target radius (0.035 m) due to pose drift, leaving the puck just outside.
*Fix:* Reduce `MAX_PUSH_PER_STEP` from 0.015 m to **0.010 m** (line 7) to keep pushes within the target radius.

**Mode 3: Gripper collision on descent (15% of failures)**
*Episodes:* 4000 (end), 4001 (end)
*Root cause:* Descent by `-0.0125 m` (line 55) moves the tool into the puck; the “too wide to grasp” constraint means side contacts lift the robot, and the `except` recovery (lines 58‑60) does not guarantee a safe re‑approach height before the next push.
*Fix:* After a descent exception, explicitly move `approach_z` up by 0.01 m before the next iteration (add after line 60).