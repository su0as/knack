**Mode 1: Contact pose out of reachable workspace**  
*Episodes: 4000–4004 (5/8)*  
*Root cause:* `contact_pos` computed at line 61 places the robot at `x ≈ 0.09–0.15`, which after clamping (lines 64–68) still risks being near joint limits or fixture collisions. The subsequent `move_to` succeeds, but the gripper cannot achieve a stable purchase.  
*Fix:* Increase `contact_offset` from `0.05` to `0.08` at line 60 to push the contact point farther from the puck edge, giving more margin for finger closure.

**Mode 2: Grasp failure due to insufficient contact quality**  
*Episodes: 4005–4007 (3/8)*  
*Root cause:* After the first `grasp()` fails (line 92), the fallback drops the target `z` by only `0.004` m (line 95). The puck’s flat top surface likely offers poor friction, and the tiny drop does not reorient fingers sufficiently.  
*Fix:* Increase the drop increment to `0.010` m at line 95, allowing fingers to re-engage from a slightly different angle before the second `grasp()` attempt.