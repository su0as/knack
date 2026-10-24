**Mode 1: Red cube missed (5 episodes: 1000, 1004, 1006, 1007 + 1 partial)**
*Root cause:* Grasp fails because the cube pose z is near table height (0.011–0.021) and the approach moves to `lift_height=0.10` then descends to `grasp_z = cube_z + 0.02`. This often places the hand too low or collides with the table. **Line 54** adds `grasp_offset` to a noisy z that can be <0.015, making `grasp_z` ≈0.035, within table collision range.
*Fix:* Clamp `grasp_z` to a minimum of `0.05` above the perceived cube centre: `grasp_z = max(cube_pose['pos'][2] + 0.02, cube_pose['pos'][2] + 0.05)`.

**Mode 2: Blue cube missed (4 episodes: 1002, 1003, 1006, 1007)**
*Root cause:* After releasing the red cube, the robot moves to the blue tray pose obtained at perception time (line 31). If the red placement perturbed the tray or the blue pose is noisy, the subsequent `move_to` overshoots. **Line 73** targets `above_tray` using the initial tray pose; any drift causes the arm to miss the tray opening.
*Fix:* Re-query the tray pose just before the place move (after lifting the cube) and recompute `above_tray`.

**Mode 3: Both cubes missed (2 episodes: 1001 succeeds, 1005 succeeds; failures in 1000–1007 show one cube often placed, the other not)**
*Root cause:* The loop processes cubes sequentially. A failed grasp or place for the first cube leaves the gripper empty or holding the wrong object, and the second cube perception may be skipped or mis‑matched. **Lines 21–35** continue the loop regardless of prior failure, so a stuck gripper prevents the second pick.
*Fix:* Add `if robot.holding() is not None: robot.release()` at the start of each cube iteration (after line 22) to ensure a clean state before the next pick.