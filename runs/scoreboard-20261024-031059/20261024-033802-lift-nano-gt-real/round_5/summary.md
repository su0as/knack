**Mode 1: Pre‑grasp too low → grasp fails**  
*Episodes:* 5000, 5002, 5005 (3/7)  
*Root cause:* The pre‑grasp height calculation (line 60‑61) forces `pre_grasp_z_raw` down to 0.008 m, then applies the safety margin. For cubes sitting near the table (`cz ≈ 0.015 m`), the resulting `pre_grasp_z` drops to ~0.016 m, leaving insufficient approach clearance for the gripper to close.  
*Fix:* Raise the floor in line 60 from `0.008` to `0.020` m, ensuring a minimum 5 mm clearance above even the flattest observed cubes before the grasp attempt.

**Mode 2: Lift height insufficient after grasp**  
*Episodes:* 5000, 5002, 5005 (same 3) – grasp succeeded but cube remained at ~0.015 m.  
*Root cause:* Line 98‑99 computes `lift_z_raw = REQUIRED_Z + cz`. When `cz` is ~0.015 m, `lift_z_raw` ≈ 0.080 m, but the subsequent `max(REQUIRED_Z, lift_z_raw)` correctly caps at 0.065 m. However, the observed final `z` (~0.015 m) indicates the robot never actually reached the lift pose; the grasp itself failed or slipped, so the lift step was never executed.  
*Fix:* Add a pre‑grasp height guard: if `cz < 0.025`, skip the grasp and retry with a higher `pre_grasp_z` (line 61), preventing attempts on objects too close to the table.