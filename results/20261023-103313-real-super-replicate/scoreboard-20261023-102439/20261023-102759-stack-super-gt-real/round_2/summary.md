**Mode 1: Grasp failure (5 episodes)**
*Root cause:* Insufficient approach depth or cube pose mismatch prevents reliable enclosure. Lines 58‑71 retry grasp twice, but if the arm arrives off‑axis or too high, the gripper slips.
*Fix:* Before each grasp attempt, move to `z = red_pos[2] + 0.01` (above cube center) using `safe_move(z=...)` to ensure proper approach angle.

**Mode 2: Collision during descent (3 episodes)**
*Root cause:* `safe_move` to `grasp_pos[2]` (cube bottom) impacts the opposite cube or workspace boundary. Lines 74‑78 lower red cube onto blue cube without checking interference.
*Fix:* Add a pre‑descent check: `if red_pos[2] < blue_pos[2] + 0.04: safe_move(dz=-0.02)` at line 74 to back off before lowering.

**Mode 3: Safety violation (1 episode)**
*Root cause:* Target `z = -0.010 m` falls below the safe workspace `[0.014, 0.26]`. Line 47 passes a negative `z` when `grasp_pos[2]` is computed from a mis‑perceived cube pose.
*Fix:* Clamp `z` in `safe_move` calls: `z = max(grasp_pos[2], 0.015)` before line 47 to keep all moves within limits.