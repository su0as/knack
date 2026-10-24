**Mode 1: Approach collision (50%)**
- **Episodes:** 4000, 4001, 4003, 4004, 4005
- **Root cause:** `safe_move` descends to `release_z` (line 105–109) but the tray approach (line 98–102) uses the same `speed=0.07`. When the arm is already holding a cube, the lowered release height brings the gripper into collision with the tray or table edge before the slower descent can clear it. The retry loop (lines 39–59) then fails because `cur_z` cannot drop further.
- **Fix:** Increase clearance above tray before descent (line 97: change `0.020` to `0.030`). This gives the arm room to transition from hover to release height without hitting the tray.

**Mode 2: Grasp failure after approach (30%)**
- **Episodes:** 4002, 4006
- **Root cause:** `safe_move` stops short (lines 46–52) and retries with reduced speed and lower `z` (lines 54–57). After two trials the arm is too low to reach the object, so `grasp()` never executes (line 76) and the cube remains untouched.
- **Fix:** Raise the initial approach `z` by 0.005 m (line 69: `approach[2] += 0.010` instead of `0.005`) to give the retry loop more room before hitting the safety minimum.

**Mode 3: Hold verification missed (20%)**
- **Episodes:** 4002, 4004, 4005
- **Root cause:** When `grasp()` succeeds but the object shifts during the tray descent (lines 105–110), `robot.holding()` (line 92) may no longer match `obj_name`, causing an early `False` return even though the cube is physically in the gripper.
- **Fix:** Add a brief `robot.wait(0.1)` after `robot.release()` (line 113) before the micro‑adjust move (line 116) to let the cube settle and stabilize the hold state.