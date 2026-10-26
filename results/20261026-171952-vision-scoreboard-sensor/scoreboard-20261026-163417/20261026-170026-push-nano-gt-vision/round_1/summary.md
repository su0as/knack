**Mode 1: Contact failure (55 episodes)**
*Root cause:* The contact pose computed at line 59 places the hand too close to the puck edge or outside the robot’s reachable workspace, causing `grasp()` to return False. The subsequent height reduction (lines 83, 124) is insufficient to establish contact.
*Fix:* Increase `contact_offset` from `0.02` to `0.04` (line 58) and add a pre-grasp height check: before closing fingers, verify `cz >= puck_z + radius + 0.015`. If not, raise `cz` by `0.01` before attempting `grasp()`.

**Mode 2: Motion blocked short (22 episodes)**
*Root cause:* `move_to` at lines 73/83/125 stops short due to collision with the table edge or joint limits when the contact pose is near workspace boundaries (clamped at lines 62–66).
*Fix:* Wrap `move_to` calls in a try/except that reduces `cz` by `0.005` and retries once. Additionally, loosen the `clamp_pose` ceiling from `0.26` to `0.28` to give more clearance for high approaches.