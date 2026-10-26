**Mode 1: Pick failure (5 episodes, seeds 3000–3004)**  
*Root cause:* The robot moves to the pick pose but the grasp is not detected as holding the red cube. The verification loop (lines 71–89) retries release and re‑approach, yet all attempts fail, leaving the gripper empty.  
*Fix:* Increase the approach speed or add a small vertical offset (e.g., `+0.01 m` in `place_z`) before closing the gripper to ensure the fingers contact the cube.

**Mode 2: Place pose unreachable (2 episodes, seeds 3006–3007)**  
*Root cause:* `move_to` to the computed `place_x, place_y, place_z` raises `MotionError` (lines 99–102). The XY offset (`offset_x=0.02`) combined with cube poses places the target outside the robot’s workspace or collides with the environment.  
*Fix:* Reduce the XY offset to `0.005 m` and/or add a check that `place_z` does not exceed the robot’s maximum Z limit before attempting the move.