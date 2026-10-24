**Mode 1: Approach timeout (2 episodes)**
*Episodes: 3001, 3004*
*Root cause:* The `move_to` to descent height (line 55) or lift (line 76) exceeds the 45s budget, likely because the calculated `cx/cy` clamp restricts the robot to a narrow corridor that is physically unreachable or obstructed, causing repeated retries.
*Fix:* Widen the clamp bounds on lines 31-32 (e.g., `0.05` → `0.02`, `0.31` → `0.35`) to give the robot more lateral room to reach the approach point without timing out.

**Mode 2: Contact/blocked descent (2 episodes)**
*Episodes: 3005, 3001 (t=43)*
*Root cause:* The push height descent (line 55) commands `0.02` m, but the puck radius plus margin pushes the approach point near obstacles. The robot "stopped short" (error_m 0.01) indicating a collision or joint limit before reaching `0.02` m (lines 56-61).
*Fix:* Reduce descent depth to `0.01` m on line 55, or add a pre-check: if `dist < 0.05`, skip the low-height move and push from the approach height directly.