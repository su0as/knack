**Mode 1 – Height shortfall (5 episodes)**
*Root cause:* `lift_target_z` is set to 0.06 m, but the final `move_to` lands at ~0.056 m (see seed 1000 trace `t=3.0 pos: [0.1591, 0.0282, 0.0597]`). The 0.004 m gap between commanded 0.06 m and observed 0.056 m violates the ≥5 cm requirement.
*Fix:* Change `lift_target_z = 0.065` on line 29 to guarantee ≥5 cm clearance even with pose error.

**Mode 2 – Grasp‑then‑lift sequencing (3 episodes)**
*Root cause:* After `grasp()` the robot immediately lifts without verifying the cube is securely held at the pre‑grasp height. If the gripper closes on a tilted cube, the lift drops the object to ~0.056 m before the final move (seeds 1000‑1006).
*Fix:* Insert a `robot.move_to(x_obj, y_obj, pre_grasp_z, ...)` after `grasp()` (after line 55) to re‑establish the 6 cm stance before the final lift on line 64.

**Mode 3 – Pose estimation noise (2 episodes)**
*Root cause:* `get_pose` returns z≈0.015 m; the pre‑grasp target 0.06 m is computed from this noisy base. Small errors propagate, leaving the cube at 0.056 m after lift.
*Fix:* Add a safety margin: set `pre_grasp_z = 0.07` on line 27 and `lift_target_z = 0.075` on line 29.