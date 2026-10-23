**Mode 1: Descent blocked (5 episodes: 1003, 1004, 1005, 1007)**
- **Root cause:** The robot attempts to move to `place_z = blue_pos[2] + 0.03` (line 79) but the target z is too low, causing a collision/contact stop before reaching the cube. Seed 1004 succeeds on first attempt because the initial `place_z` happens to clear obstacles.
- **Fix:** Increase `place_z` clearance to `blue_pos[2] + 0.05` (line 79) to guarantee safe descent over the blue cube.

**Mode 2: Grasp failure (2 episodes: 1006, 1007)**
- **Root cause:** The grasp loop (lines 49‑56) retries twice, but if the gripper opens too wide or contacts the blue cube, `holding()` returns `None`. Seed 1007 logs “safety clamps: 1”, indicating mechanical interference.
- **Fix:** Add a pre-grasp `safe_move(dz=0.02)` (after line 60) to lift the red cube slightly, avoiding collision with the blue cube during closure.

**Mode 3: Pose drift (1 episode: 1003)**
- **Root cause:** After a failed place, the robot re-homes and perceives shifted cube positions (line 23), leading to large xy offsets (0.0346) on subsequent attempts.
- **Fix:** Freeze cube poses after first successful perception (line 23) or add a `robot.wait(0.5)` before `observe()` to let vision stabilize.