**Mode 1: Perception failure (35%)**
- **Episodes:** 2001, 2002, 2005, 2007
- **Root cause:** Line 91 `robot.get_pose('puck')` raises `PerceptionError` when the puck is occluded. The code does not retry or fallback.
- **Fix:** Add a visibility guard before line 91. If `get_pose` fails, re‑approach from a different yaw or abort gracefully instead of crashing.

**Mode 2: Insufficient push distance (50%)**
- **Episodes:** 2000, 2003, 2004, 2006
- **Root cause:** Line 76 `push_distance = 0.05` (5 cm) is too short. The puck stops at 0.10 m from the target, exceeding the 0.035 m tolerance.
- **Fix:** Increase `push_distance` to ≥ 0.12 m (or loop until the puck is within tolerance), ensuring each push moves the puck far enough in one or two iterations.

**Mode 3: Release before target reached (15%)**
- **Episodes:** 2000, 2003, 2004
- **Root cause:** Line 105 `robot.release()` executes after the push loop (lines 78‑100) without checking if the puck entered the target. The loop may exit after two pushes without success, yet the gripper opens immediately.
- **Fix:** Move the release (line 105) inside the success branch (after line 96) or add a post‑push distance check before releasing.