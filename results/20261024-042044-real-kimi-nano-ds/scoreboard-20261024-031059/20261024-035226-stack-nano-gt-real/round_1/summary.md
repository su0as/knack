**Mode 1: Perception failure (5 episodes)**
*Root cause:* `observe()` returns stale or missing object data. The code at line 18 skips the sequence if `red` or `blue` is `None`, but perception noise causes false negatives, aborting valid attempts.
*Fix:* Add a perception sanity check before the loop: if objects are missing, log a warning and retry the observation once before giving up.

**Mode 2: Grasp failure (4 episodes)**
*Root cause:* `grasp()` at line 34 closes on an unstable pose or the cube slips. Verification at line 35 fails, triggering a full reset via `continue`. The retry loop then starts from perception, compounding error.
*Fix:* Insert a small `move_by(dz=0.01)` at line 33 after `grasp()` to seat the cube, then re-verify holding before proceeding.

**Mode 3: Place/Release failure (3 episodes)**
*Root cause:* `move_to()` at line 51 overshoots or collides, leaving the red cube offset. `release()` at line 58 executes despite the cube not being correctly positioned, causing it to slip or remain in the gripper.
*Fix:* Before `release()`, validate `xy_offset` from perception is < 0.02m. If not, abort and retry the placement move (line 51) rather than releasing.