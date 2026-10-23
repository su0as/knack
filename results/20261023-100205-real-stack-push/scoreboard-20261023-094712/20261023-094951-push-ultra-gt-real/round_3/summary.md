**Mode 1: Missing puck data (5 episodes)**
- **Root cause:** `puck["size"]` is absent from the observation at `t=0.0`. Line 28 crashes before any push logic runs.
- **Fix:** Guard the radius extraction. If `"size"` is missing, default `puck_radius = 0.04` (standard puck) and log a warning.

**Mode 2: Puck stops short of target (5 episodes)**
- **Root cause:** `push_distance` caps at `dist_to_target + 0.05` (line 65), which may be insufficient to clear the target radius given the 0.02 margin. The puck settles just outside.
- **Fix:** Increase the cap to `dist_to_target + 0.10` or remove the cap entirely, ensuring the puck travels far enough past the target.

**Mode 3: Edge-on puck misalignment (noted in logs)**
- **Root cause:** When `|yaw| ~ π/4`, `face_on < 0.5` raises `approach_dist` and `push_z`, but the lead angle correction (line 44) may be inadequate, causing the puck to slide sideways rather than push forward.
- **Fix:** Increase the lead angle multiplier from `0.6` to `0.8` or add a secondary correction that rotates `push_dir` away from the edge-on axis based on `puck_yaw` magnitude.