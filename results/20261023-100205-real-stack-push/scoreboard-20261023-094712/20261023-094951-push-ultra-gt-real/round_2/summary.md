**Mode 1: Start-position timeout** (seeds 2000, 2001, 2003, 2005)  
*Count: 4*  
*Root cause:* The robot repeatedly collides or hits joint limits moving to `start_xy` at `local_push_z` (line 70). The start position is often near workspace edges or behind the puck in a direction that forces the arm into its limited horizontal band (0.019–0.251 m).  
*Fix:* Reduce `approach_base` from 0.05 to 0.03 (line 18) so `start_xy` moves closer to the puck, keeping the arm within its reachable band.

**Mode 2: End-position timeout** (seed 2004)  
*Count: 1*  
*Root cause:* `end_xy` computes a push distance that places the target far outside the arm’s horizontal reach (line 63–65). The wrist target becomes unreachable (error at line 77).  
*Fix:* Cap `push_distance` at `dist_to_target + 0.05` (line 63) to keep the end position inside the 0.10–0.251 m reachable band.

**Mode 3: Upright puck, near-miss** (seeds 2006, 2007)  
*Count: 2*  
*Root cause:* Puck is upright (`face_on ≥ 0.5`) but slides sideways because `lead_angle` (line 42–43) is too small for the given `dist_to_target`, leaving the puck off‑target after the push.  
*Fix:* Increase `lead_angle` scaling: replace `puck_radius / max(dist_to_target, 0.01)` with `0.6 * puck_radius / max(dist_to_target, 0.01)` (line 42) to add more corrective yaw on every push.