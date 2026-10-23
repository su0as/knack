**Mode 1: XY misalignment during stack descent**
*Episodes: 1 (seed 2002)*
*Root cause:* Line 78 moves to `LIFT_Z` using the blue cube's yaw, but the red cube was grasped with its own yaw (line 22). The pose mismatch causes the arm to descend offset from the target. The `move_to` at line 87 then targets the wrong XY location.
*Fix:* Store the red cube's yaw at grasp (line 18) and use it for the approach-to-stack transition (lines 78/87), or re-observe the red cube's pose after lifting (line 59) before descending.

**Mode 2: Premature release / z-gap error**
*Episodes: 1 (seed 2002)*
*Root cause:* Line 96 releases at `target_z` (≈0.050m). The blue cube is only 0.015m tall; the red cube center sits at ~0.045m (line 8). Releasing at 0.050m leaves a 0.035m gap, inconsistent with the expected 0.0297m gap seen in successes, causing the red cube to rest at z=0.015m (on top of blue) but not stacked correctly, leading to `red_held=False` in checks.
*Fix:* Lower the release target to `STACK_Z` (line 8) or `STACK_Z + STACK_CLEARANCE` (line 85) to ensure the red cube seats on the blue cube before release.