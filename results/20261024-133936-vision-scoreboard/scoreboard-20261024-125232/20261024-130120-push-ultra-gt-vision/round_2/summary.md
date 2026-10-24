**Mode 1: Overshoot & undershoot (5 episodes: 2000, 2001, 2005, 2006, 2007)**
*Root cause:* The `push_dist` formula (line 55) adds a fixed `0.02` margin regardless of distance. For short pushes this margin is disproportionate, sending the puck past the target. For long pushes the puck stops short due to friction/wear.
*Fix:* Replace the fixed `0.02` with a proportional margin, e.g., `0.02 * (dist / 0.3)`, so the overshoot scales with travel distance.

**Mode 2: Gripper collision / grasp failure (1 episode: 2002)**
*Root cause:* The puck is too wide to grasp, yet the code attempts `move_to` into the puck's start zone. The gripper collides, the puck is lifted and carried (shown by "gripper holding puck"), then dropped far from target (line 51 start position uses `puck_radius + CLEARANCE`).
*Fix:* Remove the initial `move_to` to start position (lines 64-71). Begin each attempt directly at the push phase, or use a wider `CLEARANCE` value to keep the robot clear of the puck's silhouette.