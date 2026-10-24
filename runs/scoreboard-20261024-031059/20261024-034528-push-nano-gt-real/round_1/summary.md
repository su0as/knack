**Mode 1: Overshoot & drift** (5 episodes, seeds 1004–1005)  
*Root cause:* Push step (line 40) is capped at 2 cm, but the puck starts >3 cm from the target. The robot pushes the full step, then lifts (line 56) before the puck settles, leaving residual drift.  
*Fix:* Reduce `push_step` to `min(0.01, dist_to_target)` so pushes are tiny and the puck has time to settle before lift.

**Mode 2: Approach mis‑alignment** (3 episodes, seeds 1000–1003)  
*Root cause:* The approach height (line 19) adds `puck_radius + 0.0125`, but the puck is “too wide to grasp.” The tool may collide with the puck sides, causing the robot to stop short (traces show z‑values ~0.05–0.06 m instead of touching).  
*Fix:* Lower `approach_z` offset to `puck_pos[2] + 0.005` to pass above the puck centre without side interference, then rely on the touch‑z calculation (line 27) to descend safely.

**Mode 3: Insufficient correction** (all seeds)  
*Root cause:* After the push (line 44‑48) the skill lifts immediately (line 55‑58) without a second observe‑adjust loop, so any push error persists.  
*Fix:* Add a brief `observe()` after lift (after line 58) and, if `final_dist > target_radius`, retry the push with a fresh `push_step` before returning.