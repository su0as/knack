**Mode 1: Grasp failure (all seeds)**
- **Episodes:** 7
- **Root cause:** `robot.grasp()` returns `holding: null` (lines 61, 66). The gripper closes but fails to acquire the cube, likely due to pose misalignment or insufficient downward force.
- **Fix:** Add a pre-grasp alignment check. Before closing, move to `grasp_z - 0.02` to validate contact, then descend. Alternatively, increase `grasp_offset` from `0.05` to `0.10` (line 44) to lower the closure point.

**Mode 2: Tray–cube colour mismatch (seeds 3001–3005)**
- **Episodes:** 5
- **Root cause:** `colour_to_tray` mapping uses `fix['color']` (line 17). Perception assigns tray colours incorrectly or cubes have non-standard colours, so `tray_name` is `None` or wrong, causing placement into the wrong tray or skip.
- **Fix:** Log the detected tray colour at line 17 and validate that `colour` matches before picking. If mismatch, abort and request human correction.

**Mode 3: Tray pose drift during execution (seeds 3000–3007)**
- **Episodes:** 7
- **Root cause:** Tray pose is fetched once at line 31 but refreshed only at line 75 inside `_pick_and_place`. If the robot moves the cube, the stored `tray_pose` becomes stale, causing the release offset (line 80) to miss the target.
- **Fix:** Move the `robot.get_pose(tray_name)` call (line 75) to immediately before the `move_to` at line 77, ensuring the latest perception is used for placement.