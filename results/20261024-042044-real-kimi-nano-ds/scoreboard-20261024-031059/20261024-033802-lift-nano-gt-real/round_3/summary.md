**Mode 1 – Grasp failure (6 episodes)**
- **Root cause:** `robot.grasp()` returns `holding: null` at lines 75‑78. The gripper never closes on the cube.
- **Fix:** Increase `SPEED_LIFT` or add a brief `robot.wait(0.05)` after `robot.move_to` before `robot.grasp()` to ensure the arm settles on the cube before closing.

**Mode 2 – Pre‑grasp position missed (4 episodes)**
- **Root cause:** `move_to` targets `z=0.055` (line 58) but the cube base `cz` is only ~0.015 m. The pre‑grasp pose may not contact the cube, causing the gripper to miss.
- **Fix:** Set `PRE_GRASP_Z = cz - 0.002` (use observed base height) so the arm descends to the cube top before closing.

**Mode 3 – Lift height insufficient (0 episodes, but check)**
- **Root cause:** `lift_z = REQUIRED_Z + cz` (line 88) adds observed base height; if `cz` is mis‑reported the final `final_z` may fall below 0.065 m (line 110).
- **Fix:** Clamp `lift_z = max(lift_z, REQUIRED_Z)` before the lift move to guarantee the safety margin regardless of observation noise.