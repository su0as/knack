**Mode 1: Contact-limited approach (6 episodes, seeds 2000–2002, 2006)**
*Root cause:* The robot lowers to `contact_height` (line 72) but the puck’s geometry or orientation causes the gripper to hit the table or puck edge before full descent, triggering the exception handler (line 73–76) which retreats to `lift_height`. The puck never enters the push phase.
*Fix:* Increase `base_contact_height` from `0.02` to `0.03` m. This provides more clearance for the approach and reduces premature contact stops.

**Mode 2: Lateral misalignment at close range (3 episodes, seeds 2001, 2006, 2007)**
*Root cause:* When `dist_xy < 0.05` m (line 53), the code attempts a lateral side-step (lines 55–56). However, the step size `0.02` m is insufficient when the puck is already near the target radius, causing the robot to reposition into a blocked configuration or fail to re-establish contact.
*Fix:* Increase the lateral step to `0.04` m in the close-range reposition block (lines 55–56) to ensure a clear path around the target perimeter.