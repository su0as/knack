**Mode 1: Insufficient lift height** (7 episodes)  
*Root cause:* The lift command targets `lift_z = cz + 0.065` (line 21), but the cube centre `cz` is measured from the observed pose. Due to sensor noise or initial descent error, the final cube z-coordinate settles around 0.064 m, just below the 0.065 m threshold checked at line 56.  
*Fix:* Change the lift target to `cz + 0.070` (line 21) to provide a 7 cm clearance, ensuring the verification at line 56 passes even with small pose drift.

**Mode 2: Grasp fails to close fully** (2 episodes, seeds 1001, 1002)  
*Root cause:* The grasp attempt (line 36) succeeds (`holding: "red_cube"`), but the gripper opening remains wide (≈0.027 m), indicating an incomplete closure. The cube then slips during lift, dropping below the height check.  
*Fix:* Insert a brief `robot.wait(0.2)` after `robot.grasp()` (after line 36) to allow the gripper to seat fully before lifting.

**Mode 3: Early release during descent** (1 episode, seed 1001)  
*Root cause:* After a failed grasp at line 36, `robot.release()` is called (line 38) and the episode retries, but the subsequent descent (line 31) uses the same `grasp_z` computed from a stale observation, causing a collision or loss of the cube.  
*Fix:* Reset the observation before retrying: add `obs = robot.observe()` at the start of the loop body (after line 6) to ensure `grasp_z` reflects the current cube pose.