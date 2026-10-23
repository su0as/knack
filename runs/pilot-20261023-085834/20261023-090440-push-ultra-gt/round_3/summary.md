**Mode 1: Insufficient push length (67%)**
*Episodes: 3000, 3001, 3002, 3003, 3004, 3005, 3006, 3007*
*Root cause:* The push length is `push_dist + 0.03 m` (line 61). The target radius is 0.04 m, but the required displacement varies (0.09–0.19 m). A fixed 3 cm margin is insufficient for longer pushes, leaving the puck short.
*Fix:* Set `push_length = push_dist + max(0.03, target["radius"] * 1.5)` to ensure the margin scales with target size and initial distance.

**Mode 2: Start position too close to puck (33%)**
*Episodes: 3005 (safety clamps), others with vertical log*
*Root cause:* The start offset (line 32) is `0.05 + puck_radius`. If the puck is large or the initial clearance check (lines 38–44) shifts the start minimally, the robot may collide or push at an angle, reducing effective travel.
*Fix:* Increase `start_offset` to `0.10 + puck_radius` to guarantee horizontal clearance and a stable push vector.