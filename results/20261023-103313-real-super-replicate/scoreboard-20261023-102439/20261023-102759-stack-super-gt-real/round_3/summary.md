**Mode 1: Grasp failure (2 episodes, seeds 3001, 3004)**  
*Root cause:* Descent to grasp height overshoots or stops short due to joint limits/contact, preventing closure. Seed 3001 descends to z=0.017 (line 66) and succeeds, but seed 3004 stops at z=0.016 (line 66) and later at z=0.022 (line 83) with error_m 0.0168, indicating the robot cannot reach the target pose.  
*Fix:* Lower `grasp_z` clamping floor to `0.010` (line 12) and add a retreat check after `robot.grasp()` (line 74) to verify `holding()=='red_cube'` before lifting; if not, retreat to `SAFE_Z` (line 82) immediately rather than looping.

**Mode 2: Place mis‑alignment (2 episodes, seeds 3005, 3006)**  
*Root cause:* Release occurs at `place_z = blue_pos[2] + 0.03` (line 109) which sets the red cube centre at ~0.045 m. The verification tolerance `POS_TOL=0.02` (line 7) then fails if the red cube settles slightly off‑center or the blue cube shifts during release.  
*Fix:* Reduce `place_z` offset to `0.025` (line 109) so the red cube sits lower, and increase `POS_TOL` to `0.03` (line 7) to accept minor settling variance.

**Mode 3: Stack collision / joint limit (1 episode, seed 3005)**  
*Root cause:* Moving above blue cube (line 102‑103) from a distant pre‑grasp pose causes a joint limit when descending to `place_z`. The trace shows a successful release despite the error, but the subsequent verify fails.  
*Fix:* After `safe_move_to` above blue cube (line 103), add a `robot.wait(0.1)` and re‑check `obs['objects']['blue_cube']` position before descending; if the pose changed, re‑perceive (line 38) before proceeding.