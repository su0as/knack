**Mode 1: Perception/contact failure** (seeds 4000, 4003, 4005, 4006, 4007; 5 episodes)  
*Root cause:* The gripper closes but `holding()` returns `None` (line 68), so the tiny downward press (line 70) also fails. The puck slides without being pushed.  
*Fix:* Increase the press depth or add a lateral nudge (e.g., `move_by(dx=0.002, dy=0)` before `grasp()`) to ensure finger‑puck contact.

**Mode 2: Workspace‑y violation** (seeds 4001, 4002, 4004, 4006, 4007; 5 episodes)  
*Root cause:* `push_distance` computation (lines 84‑93) does not clamp the x‑component, allowing `new_x` to exceed the 0.04–0.32 m range (line 98) or `contact_y` to drift outside [-0.26, 0.26] (line 47). Seed 4002 explicitly violates the y‑clamp at line 106.  
*Fix:* Add x‑margin checks analogous to y‑margins (lines 84‑85) and enforce `0.04 <= new_x <= 0.32` before `move_by` (line 98).

**Mode 3: Reach/over‑extension** (seeds 4004, 4005; 2 episodes)  
*Root cause:* Push distance accumulates beyond the arm’s horizontal reach (0.10–0.251 m, line 7.58 trace) or contact point moves outside the safe x‑range, causing `MotionError` (line 108).  
*Fix:* Cap `push_distance` by the remaining x‑margin (`0.32 - contact_x`) and reset contact pose after each push to prevent cumulative drift.