**Mode 1: Contact-blocked approach (55 episodes)**
*Root cause:* The contact pose computation (line 61) places the robot too close to fixtures or edges, causing `move_to` to stop short (note: "stopped short of the target (blocked by contact or joint limit)" at lines 83, 95). The 0.01m offset is insufficient for puck radius clearance.
*Fix:* Increase `contact_offset` from 0.01 to **0.05** (line 60) to push the contact pose farther from the puck surface, reducing fixture interference.

**Mode 2: Grasp failure (22 episodes)**
*Root cause:* `grasp()` returns `False` (lines 92–101). Logs show "grasp returned False – first attempt" followed by height drop attempts that still fail, leaving the puck ungripped and unable to push.
*Fix:* Widen the gripper opening threshold in the perception step or add a pre-grasp approach offset (line 61) to ensure the fingers close on a stable surface before closing.

**Mode 3: Push undershoot (all episodes)**
*Root cause:* `move_by` uses `push_dist_norm` (line 105), but the puck radius and surface friction reduce effective displacement. The final `check` values (~0.12m) exceed the 0.035m tolerance, indicating the puck does not reach the zone centre.
*Fix:* Scale the push distance by **0.7** (line 108) to `dx * 0.7` and `dy * 0.7` to compensate for slippage, or add a second small push after release if the first undershoots.