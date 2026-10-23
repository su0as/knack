**Mode 1: Overshoot / undershoot (5 episodes: 4000, 4001, 4004, 4005, 4006)**
*Root cause:* `push_dist` on line 68 adds `offset` (puck radius + clearance) to the *remaining distance* to target. The puck is pushed past the target because the offset is applied after the distance, not as a pre‑push approach adjustment.
*Fix:* Change line 68 to `push_dist = dist2 + margin` and move the offset handling to the stand‑off positioning (lines 38‑40).

**Mode 2: Missed puck / wrong trajectory (3 episodes: 4002, 4003, 4007)**
*Root cause:* The re‑observation at line 53 captures puck position *after* the gripper has already moved to the stand‑off point (line 47). If the puck shifted during the approach, the subsequent push vector (lines 56‑62) is computed from a stale or altered pose, causing a miss.
*Fix:* Re‑observe immediately before computing the push vector (after line 50) and before moving to the push target (line 71), ensuring `puck_pos2` reflects the true current pose.