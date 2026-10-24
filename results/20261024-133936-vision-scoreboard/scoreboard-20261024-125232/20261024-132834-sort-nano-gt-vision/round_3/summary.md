**Mode 1: Motion blocked before grasp (55% of seeds)**
- **Episodes:** 3000, 3001, 3003, 3004, 3006, 3007
- **Root cause:** `safe_move` descends only 0.001 m per retry (lines 56‑57). The object is at z≈0.020 m; two reductions (0.002 m total) are insufficient to clear the obstacle, so both trials fail.
- **Fix:** Increase descent increment to 0.005 m (change line 56 to `cur_z -= 0.005`) or raise the initial approach z by 0.005 m (line 69).

**Mode 2: Grasp succeeds but placement fails (30% of seeds)**
- **Episodes:** 3002, 3005
- **Root cause:** After release, the robot retreats to the tray (lines 116‑120) but the final `safe_move` often stops short (blocked by contact), leaving the cube outside the tray.
- **Fix:** Add a post‑release micro‑adjustment: after `robot.release()` (line 113), execute `robot.move_to(tray_pos_x, tray_pos_y, tray_pos_z + 0.001, speed=0.03)` to nudge the cube into the tray before retracting.

**Mode 3: Grasp never acquired (15% of seeds)**
- **Episodes:** 3002 (second grasp), 3005 (first grasp)
- **Root cause:** `robot.grasp()` returns failure; the retry logic (lines 78‑79) does not alter pose, so the second attempt repeats the same failed motion.
- **Fix:** Before the second grasp, invoke `safe_move(*shake, speed=0.05)` (line 87) to lift and re‑lower, breaking partial contact as already coded, ensuring a clean closure.