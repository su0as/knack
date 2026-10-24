**Mode 1: Perception‑driven push short** (seeds 5000, 5001, 5002, 5005, 5006, 5007)  
*Count: 6*  
Root cause: The push distance is capped by workspace margins (lines 85‑106) but the desired 0.12 m push is often truncated before the puck reaches the target, leaving a residual error >0.035 m.  
Fix: After each `robot.move_by` (line 120), recompute the remaining distance to target and, if still >0.035 m, issue a second `robot.move_by` with the leftover vector rather than aborting.

**Mode 2: Gripper contact failure** (seeds 5000, 5001, 5002, 5005)  
*Count: 4*  
Root cause: The approach move (line 58) may miss the side‑on contact point, and the subsequent tiny nudge + `robot.grasp()` (line 69) does not guarantee finger‑puck contact; `robot.holding()` can remain `None` (lines 70‑75).  
Fix: Before the nudge, verify `contact_x, contact_y` lie within the puck’s bounding radius; if not, adjust `side_offset` (lines 37‑38) to re‑align the approach vector.

**Mode 3: Safety‑violation push** (seed 5004)  
*Count: 1*  
Root cause: The x‑margin calculation (lines 85‑91) permits a push that moves the contact point below the safe x‑min of 0.04 m, triggering the SafetyViolation at line 120.  
Fix: Add a pre‑push guard: `if new_x < 0.04: push_distance = min(push_distance, new_x - 0.04)` before executing `robot.move_by` (line 120).