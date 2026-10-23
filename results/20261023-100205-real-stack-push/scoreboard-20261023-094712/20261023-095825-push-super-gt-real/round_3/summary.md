**Mode 1: Overshoot & undershoot (6 episodes)**
*Root cause:* The push distance formula `push_dist = dist + offset + 0.02` (line 53) adds a fixed 0.02 m margin regardless of remaining distance. When the puck starts far from the target, this margin pushes the puck past the circle; when close, it falls short.
*Fix:* Cap the margin to a percentage of `dist`, e.g. `push_dist = dist + offset + 0.02 * dist`.

**Mode 2: Missed approach vector (4 episodes)**
*Root cause:* The stand‑off point is computed as `behind_x = puck_pos[0] - offset * ux` (line 39) using the *current* puck position, but perception updates between the approach and the push. The robot therefore pushes from a stale position, missing the target.
*Fix:* Re‑observe and recompute `ux, uy, behind_*` immediately before the `move_to` at line 47.

**Mode 3: Height collision (2 episodes)**
*Root cause:* `stand_off_z = 0.05` (line 43) is too low for the gripper to clear the puck when approaching from behind, causing the robot to contact the puck and stop short.
*Fix:* Increase `stand_off_z` to `0.07` and lower `push_z` to `0.025` to keep the tool clear while pushing closer to the table surface.