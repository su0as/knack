**Mode 1 – Grasp failure (6 episodes)**
*Root cause:* The contact pose places the gripper above the puck, but the `grasp()` call returns `False` and the fallback drop of 0.010 m (line 97) is insufficient to achieve contact. The puck remains ungripped, so the subsequent push moves the robot base instead.
*Fix:* Increase the fallback drop to **0.020 m** (line 97) or add a second fallback at 0.030 m before giving up.

**Mode 2 – Push distance insufficient (5 episodes)**
*Root cause:* After a successful grasp, the push displacement is scaled by 0.7 (line 107) and a second tiny push of only 0.3× the scaled vector (line 126) may not close the remaining gap. The `check` values (≈0.10 m) exceed the 0.035 m tolerance.
*Fix:* Replace the second push multiplier with **0.6** (line 126) or compute the exact remaining distance and push that amount.

**Summary:** 11/11 failures stem from grasp loss or under‑powered pushes. Adjusting the drop depth and push multipliers will likely push the puck inside the green zone.