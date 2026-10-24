**Mode 1: Approach blocked (55%)**
*Episodes:* 1000, 1001, 1002, 1003, 1005
*Root cause:* `move_to` stops short because the gripper contacts the puck edge or joint limits before reaching the computed contact point (lines 57‑66). The approach trajectory does not account for the puck’s width, so the robot cannot align its fingers with the push direction.
*Fix:* Pre‑rotate the approach pose so the gripper contacts the puck side-on rather than head‑on. Adjust `contact_x`/`contact_y` to offset toward the side facing the target, ensuring the approach vector aligns with `ux, uy` without immediate collision.

**Mode 2: Insufficient push distance (30%)**
*Episodes:* 1004, 1006, 1007
*Root cause:* `push_distance = 0.02 m` (line 76) is too short to overcome friction/initial pose variance; the puck moves < 0.04 m and stays outside the target radius.
*Fix:* Increase `push_distance` to 0.05 m and add a second push iteration if `distance` remains > 0.04 m after the first move_by.

**Mode 3: Grasp/contact mismatch (15%)**
*Episodes:* 1000‑1003 (early approach failures)
*Root cause:* `robot.grasp()` (line 71) closes fingers to 5 cm max; the puck’s width prevents a true grasp, leaving `holding: null` and no stable push vector.
*Fix:* Replace `grasp()` with a light `touch()` or `set_force(0.1 N)` to ensure finger contact without closing fully, preserving the intended push direction.