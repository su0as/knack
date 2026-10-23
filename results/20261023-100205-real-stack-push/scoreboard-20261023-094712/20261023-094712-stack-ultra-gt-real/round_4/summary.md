**Mode 1: Premature release before stacking**
* **Episodes:** 4001, 4003, 4004 (3/5 failures)
* **Root cause:** `release()` is called at `t=6.9` (seed 4001) or `t=7.28` (seed 4004) while the robot is still at `LIFT_Z` (0.12m), far above the blue cube. The stack logic has not begun; `move_to` to `STACK_Z` never executes.
* **Fix:** Move the `robot.release()` call to after the stack descent and `wait(0.1)` at line 109. Ensure release only happens at `STACK_Z` + clearance.

**Mode 2: Grasp failure / drop during transport**
* **Episodes:** 4000, 4005–4007 (5/8 successes show `red_held=False` in checks but final pos shows cube stacked; however, failures in this group likely dropped the cube before stacking).
* **Root cause:** Inconsistent grasp or transport vibration causes the red cube to slip. The code verifies `holding()` after grasp (line 58) but does not re-verify before the `move_to` at line 65.
* **Fix:** Add a hold verification check immediately before line 65: `if robot.holding() != "red_cube": robot.home(); return False`.

**Mode 3: Blue cube mis-detection / pose drift**
* **Episodes:** 4001, 4003, 4004 (failures show blue_z=0.0149, red landed at 0.015, indicating no stack).
* **Root cause:** After release at line 112, the blue cube pose observed at line 73 may have drifted or the fresh observation missed the cube due to gripper collision or camera occlusion, causing `move_to` to a wrong or missing target.
* **Fix:** Ensure the robot hovers at `LIFT_Z` with a wide field-of-view before the `observe()` at line 73, and add a check `if "blue_cube" not in obs["objects"]: continue retry` before line 80.