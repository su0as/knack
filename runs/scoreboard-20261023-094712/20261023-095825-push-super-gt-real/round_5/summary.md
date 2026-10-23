**Mode 1: gripper pose query failure** (7 episodes)
- **Root cause**: `robot.get_pose("gripper")` at line 71 queries a named fixture not registered in the simulation. The code assumes a "gripper" object exists, but only `puck` and `target` are known.
- **Fix**: Replace `get_pose("gripper")` with `robot.get_end_effector_pose()` or hardcode the gripper offset from the robot base using known kinematics.

**Mode 2: insufficient push distance** (all 8 episodes)
- **Root cause**: `push_dist` (line 79) computes `needed = dist2 - target_radius`. When the puck starts near the target, `dist2` is small, making `needed ≈ 0`. The subsequent push moves the puck only a few millimeters, failing to overcome friction or settle.
- **Fix**: Add a minimum push distance floor, e.g., `push_dist = max(0.05, needed + margin)` to ensure a meaningful displacement per attempt.