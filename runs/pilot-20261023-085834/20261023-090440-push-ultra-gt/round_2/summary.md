**Mode A: Overshoot (5 episodes, seeds 2000, 2002, 2005, 2007)**
*Root cause:* The push length adds a fixed 0.08 m margin (line 52), but the puck’s inertia and the reverse tap (line 65) are insufficient to stop exactly at the target boundary. Episodes end with `puck_to_target_xy` just above 0.035 m.
*Fix:* Reduce `push_length` margin to `push_dist + 0.03` and increase reverse tap magnitude to `0.04 m` (line 65).

**Mode B: Short push (4 episodes, seeds 2001, 2003, 2004, 2006)**
*Root cause:* Start position is computed behind the puck (line 30‑32), but the subsequent `move_to` (line 58) travels only `push_length` from that start. When the gripper yaw is misaligned (e.g., seed 2001 yaw 0.684 vs. computed), the effective push vector deviates, leaving the puck short of the target.
*Fix:* Clamp gripper yaw to the computed `gripper_yaw` (line 27) and ensure `move_to` uses the same yaw; add a debug log at line 58 to verify actual displacement.

**Mode C: Gripper collision / drop (2 episodes, seeds 2001, 2003)**
*Root cause:* The gripper yaw offset (line 27) assumes flat finger pads face the push direction. With the puck too wide to grasp, the robot may collide or fail to release, resulting in `gripper holding None`.
*Fix:* Add a pre‑push clearance check: before `move_to` at line 46, verify `start_z` clears the puck by ≥ 0.02 m; if not, raise `start_z` by 0.01 m.