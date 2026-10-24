**Mode 1: Insufficient push distance** (6 episodes, seeds 2000‑2003, 2005‑2006)  
*Root cause*: `push_step` capped at 1.5 cm (skill.py line 37) but the puck‑to‑target gap exceeds this per‑step, so the puck drifts only ~0.11 m per episode.  
*Fix*: Increase `push_step` to `min(0.03, dist_to_target)` or loop pushes until `final_dist < target_radius`.

**Mode 2: Collision‑limited approach** (5 episodes, seeds 2001‑2003, 2006‑2007)  
*Root cause*: Repeated `move_to` stops short (note “stopped short of the target”) due to joint/contact limits at low approach heights (skill.py lines 18‑22).  
*Fix*: Raise `approach_z` by 0.01 m (e.g., `puck_pos[2] + 0.015`) or add a retry that lifts 5 mm before re‑approaching.

**Mode 3: Safety violation** (1 episode, seed 2004)  
*Root cause*: `approach_z` computed as `puck_pos[2] + 0.005` can fall below the safe workspace minimum 0.014 m (skill.py line 18).  
*Fix*: Clamp `approach_z = max(approach_z, 0.014)` before the `move_to` call.