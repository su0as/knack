**Mode 1: Approach collision** (5 episodes: 3000, 3002, 3003, 3004, 3005)  
*Root cause:* `move_to` repeatedly stops short (lines 33–37). The arm contacts the puck side or workspace walls before reaching the target xy‑position, leaving the puck far from the goal.  
*Fix:* Increase `approach_z` by 0.01 m before the first `move_to` call, or add a small xy‑offset (e.g., +0.02 m in the direction of the target) to avoid side collisions.

**Mode 2: Push blocked / joint limit** (5 episodes: 3001, 3006, 3007, plus 3002/3004 tail steps)  
*Root cause:* `move_by` in the push loop (lines 66–73) aborts on the first contact, returning `False` and ending the episode. The 2.5 cm step is too large for the narrow corridor between puck and table edge.  
*Fix:* Reduce `MAX_PUSH_PER_STEP` to 0.015 m and add a retry loop: on exception, lift to `approach_z`, re‑observe, and attempt a smaller step instead of failing the episode.