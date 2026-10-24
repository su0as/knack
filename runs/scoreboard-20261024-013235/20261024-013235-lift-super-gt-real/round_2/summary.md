**Mode 1: Insufficient lift after grasp** (3 episodes: 2000, 2005)  
*Root cause*: The final lift targets `cz_refined + 0.05 + 0.001`, but `cz_refined` is extracted from a *post-grasp* observation where the cube may have settled or shifted downward. The epsilon `0.001` is too small to guarantee the 5 cm table‑clearance threshold (line 69, 80).  
*Fix*: Add a safety margin of `+0.01 m` to `target_z` (line 69) so the robot lifts to at least `cz_refined + 0.061`, guaranteeing clearance even if the cube sinks post‑grasp.

**Mode 2: Collision with safe‑workspace limits** (1 episode: 2004)  
*Root cause*: The descend step moves to `cz` (cube centre height). When the cube is near the table surface, `cz` can fall below the robot’s safe workspace floor of `0.014 m`, triggering a `SafetyViolation` (line 31).  
*Fix*: Clamp the descend target to the workspace floor: `target_z = max(cz, 0.014 + 0.01)` before `move_to` (line 31), ensuring the robot never requests a pose below `0.024 m`.