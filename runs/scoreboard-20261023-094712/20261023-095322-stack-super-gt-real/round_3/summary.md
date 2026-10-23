**Mode 1: Premature release (5 episodes: 3001, 3002, 3004, 3005, 3007)**
- **Root cause:** Release occurs at `stack_z` (centre of red cube) but the red cube centre is at `blue_z + CUBE_SIZE/2 + EPS ≈ 0.015 + 0.015 + 0.01 = 0.04`. The blue cube top is at `0.015 + 0.03 = 0.045`. Releasing at 0.04 lets the red cube fall below the blue cube before gravity settles it, causing a miss.
- **Fix:** Change `stack_z` to `blue_pos[2] + 2*CUBE_SIZE - EPS` (line 87) so release happens at the blue cube top surface.

**Mode 2: XY offset too large for stable grasp (4 episodes: 3001, 3002, 3004, 3005)**
- **Root cause:** `xy_offset` up to 0.034 m exceeds the robot’s grasp tolerance. The arm moves to the observed pose but the cube shifts slightly during the approach, causing the gripper to miss or slip.
- **Fix:** Add a secondary `observe()` and re‑compute `red_pos` immediately before `safe_move` to grasp (insert after line 68, before line 74).

**Mode 3: Grasp verification failure (1 episode: 3007)**
- **Root cause:** After `grasp()`, `holding()` returns `"red_cube"` but the cube is not securely held; release at line 98 drops it.
- **Fix:** Increase `GRASP_Z` to `HALF + 0.005` (line 19) to lift the cube slightly higher before release, giving more clearance for the stack.