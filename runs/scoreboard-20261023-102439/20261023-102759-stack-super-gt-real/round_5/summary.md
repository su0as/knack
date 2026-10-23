**Mode 1: Placement misalignment (seeds 5004, 5006)**  
*Episodes:* 2  
*Root cause:* After release, the red cube lands outside the 3 cm POS_TOL. In seed 5004 the descent to `place_z` stopped short (line 125) due to a joint limit, leaving the cube at `z=0.015` instead of the intended `0.045`. The subsequent verify (line 138‑142) flags a large `dz`.  
*Fix:* Add a post‑release `safe_move_to` to nudge the red cube into position before verification (e.g., move to `place_pos` with `speed=0.05` after `robot.release()` at line 132).

**Mode 2: Descent collision/blocked (seed 5004)**  
*Episodes:* 1  
*Root cause:* Line 125 `safe_move_to` descends to `place_z` but the robot hits a joint limit or contact, reporting `ok: false` (trace t=16.1). The code then releases the cube at that unsafe height, causing the final mis‑placement.  
*Fix:* Wrap the place‑descent in a retry loop (max 2 attempts) that retreats to `SAFE_Z` on failure before re‑trying the descent, preventing release at a blocked pose.