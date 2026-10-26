**Mode 1: Pre‑grasp height too low** (6 episodes, seeds 2000‑2005)  
*Root cause:* `PRE_GRASP_Z = obj.z + OFFSET` (line 48) uses the observed cube centre z ≈ 0.015 m plus a 0.04 m offset, yielding ~0.055 m. The subsequent descent to `GRASP_Z = 0.015 m` (line 45) leaves the gripper at table height; the final lift to `TARGET_Z = 0.055 m` (line 122) only just clears 5 cm, and perception noise (+0.004 m cube z) pushes the actual height below the required 0.065 m check.  
*Fix:* Increase `OFFSET` to 0.05 m (line 47) so `PRE_GRASP_Z` starts at ~0.065 m, eliminating the need for a deep descent and giving headroom for the final lift.

**Mode 2: Gripper closure fails at low pose** (4 episodes, seeds 2006‑2007)  
*Root cause:* The robot descends to `GRASP_Z = 0.015 m` (line 91) before closing the gripper (line 99). At this height the cube is essentially on the table, causing intermittent grasp failures that require a recovery nudge (lines 102‑103), which does not raise the cube enough to meet the 5 cm target.  
*Fix:* Remove the explicit descent to `GRASP_Z`; instead move directly to `PRE_GRASP_Z` (line 57) and close the gripper there, ensuring the cube is lifted before closure.