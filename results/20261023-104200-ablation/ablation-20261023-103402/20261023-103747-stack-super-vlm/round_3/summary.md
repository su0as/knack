**Mode 1: Release before stacking (5 episodes: 3000, 3001, 3002, 3003, 3004)**
- **Root cause:** `robot.release()` executes at line 99 while the red cube is still at the approach height (z=0.05) above the blue cube, not at the stack target height (z ≈ 0.065). The cube slides off the side.
- **Fix:** Insert a lift to `target_z + 0.015` (line 89-96 block) *before* the `release()` call at line 99. This ensures the cube is clear of the blue cube before letting go.

**Mode 2: Insufficient approach height (2 episodes: 3005, 3006)**
- **Root cause:** The approach waypoint `above_blue` (lines 67-72) uses `z: 0.05`. With cube thickness 0.03 m, the robot descends to z ≈ 0.045 for grasping, leaving only 5 mm clearance. Collisions or inaccurate poses prevent stacking.
- **Fix:** Raise `above_blue` z to `0.08` (increase clearance by 30 mm) to guarantee safe transit over the cubes.

**Mode 3: Gripper collision/retreat failure (1 episode: 3007)**
- **Root cause:** After release, the retreat move (lines 108-115) targets `z: 0.05`, which is below the stacked cube height (~0.065). The robot crashes into the stack.
- **Fix:** Change retreat `z` to `target_z + 0.015` (≈0.08) to clear the stacked cubes.