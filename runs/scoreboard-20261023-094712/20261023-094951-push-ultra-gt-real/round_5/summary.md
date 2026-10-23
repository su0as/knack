**Mode 1: Timeout on push move (5 episodes: 5001, 5002, 5003, 5006, 5007)**
- **Root cause:** The `robot.move_to` call at line 109 targets the end position with a very slow speed (0.02) and absolute yaw. When the puck is edge-on or the start position is near workspace limits, the arm traverses a long, collision-prone path or hits joint limits, exceeding the 45 s budget.
- **Fix:** Reduce `local_push_z` to the nominal `push_z` (0.02) when `face_on < 0.5`, or increase `speed` to 0.05 for the push move. This shortens traversal time and avoids unnecessary height penalties.

**Mode 2: Start position unreachable (1 episode: 5006)**
- **Root cause:** `ensure_clearance` and `clamp_xy` push the start xy to (0.229, 0.186), which lies outside the robot’s horizontal reach (0.019–0.251 m). Line 90–91 places the robot where it cannot go.
- **Fix:** After `clamp_xy`, re‑check reachability or constrain `start_xy` within `X_MAX = 0.32` but also enforce a maximum radius from the base (e.g., `np.linalg.norm(start_xy) <= 0.25`). If unreachable, shift start_dir inward before computing `start_xy`.