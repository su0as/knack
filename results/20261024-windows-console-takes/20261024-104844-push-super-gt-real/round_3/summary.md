**Mode 1: Overshoot & oscillation** (5 episodes, seeds 3000, 3001, 3002, 3004, 3005)
*Root cause:* The push distance `dist_xy + 0.002` (line 80) adds a fixed 2 mm beyond the target. When the puck is already near the target, this extra travel pushes it past the green circle, then the next perception step sees it overshot and the loop retries from a new pose, creating a drift pattern.
*Fix:* Cap the push distance to the remaining gap: `push_distance = min(dist_xy + 0.002, dist_xy * 1.1)` so the final nudge never exceeds 10 % of the gap.

**Mode 2: Lateral slip from yaw** (3 episodes, seeds 3003, 3006, 3007)
*Root cause:* When `puck_yaw > 0.1745` rad (line 41) a lateral offset is applied (lines 46‑48). The offset magnitude `0.02 * sin(puck_yaw)` is too small to counteract friction torque, so the puck tips and slides sideways instead of translating forward.
*Fix:* Increase the lateral scaling from `0.02` to `0.05` (line 46) so the push point shifts enough to keep the puck rolling straight.

**Mode 3: High approach height on close targets** (all 7 episodes)
*Root cause:* When `dist_xy < 0.05` (line 53) the code sidesteps 0.04 m laterally at `lift_height` (lines 55‑60). If the sidestep lands the gripper in a narrow corridor between puck and table, the subsequent `move_to` to `behind_x, behind_y, contact_height` (line 72) can collide, triggering the `continue` and losing progress.
*Fix:* Reduce the lateral step in the close‑target branch from `0.04` to `0.02` (line 55) to keep the gripper within the safe workspace.