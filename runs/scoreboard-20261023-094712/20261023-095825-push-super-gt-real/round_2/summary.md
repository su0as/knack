**Mode 1: Short‑stop on approach (55 episodes)**
- **Root cause:** The `move_to` to `push_z` (line 42) is blocked by contact or a joint limit before reaching the target z‑height. The robot stops short, leaving the puck un‑pushed.
- **Fix:** Increase `push_z` from 0.02 to 0.03 m (line 36) to give clearance over any minor puck tilt, or add a brief `move_by(dz=0.01, speed=0.05)` after line 42 to nudge the height up if the first move fails.

**Mode 2: Overshoot / missed push distance (12 episodes)**
- **Root cause:** `push_dist = dist + offset` (line 45) uses the full centre‑to‑centre distance, but the puck radius offset may be insufficient or the push stops early due to the “stopped short” note, leaving the puck short of the target.
- **Fix:** Add a safety margin of `+0.02 m` to `push_dist` (line 45) so the robot pushes past the nominal target centre, ensuring the puck centre reaches inside the green circle even if slip occurs.

**Mode 3: Gripper collision on retreat (8 episodes)**
- **Root cause:** After the push, `move_by(dz=0.02, speed=0.1)` (line 51) lifts the gripper, but if the puck is still contacting the gripper edges, the lift is inadequate, causing the gripper to retain the puck (reported as “gripper holding puck” in seed 2000).
- **Fix:** Increase the lift amount to `dz=0.04` (line 51) or add a small `move_by(dx=0.01, dy=0.01)` before the lift to ensure a clear vertical path.