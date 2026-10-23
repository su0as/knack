**Failure modes:**

1. **Misplaced stack (seed 2003)** — 1 episode. The robot descended to the table surface (z=0.013) instead of the cube center, then moved sideways to the blue cube's position (0.136, 0.144) and released at table height. The red cube ended beside the blue cube.
   *Root cause:* Line 39 uses `red_pose["pos"][2]` (table surface) for the grasp z-target. Line 78 computes `target_z` correctly from blue pose, but the earlier low descent caused the robot to lose the cube or release at the wrong location.
   *Fix:* Change line 39 `z: red_pose["pos"][2]` to `z: red_pose["pos"][2] + half_height` to target the cube center.

2. **Grasp/contact failure (seeds 2001, 2002, 2004, 2005)** — 4 episodes. Final positions show red cube slightly offset or tilted; all have safety clamps triggered, suggesting the robot aborted or slipped during approach/release.
   *Root cause:* Insufficient clearance or speed control during the final stack approach (lines 79-86) or release (line 99) caused the gripper to catch on the blue cube edge.
   *Fix:* Increase `lift_before_release` z-offset on line 92 from `0.005` to `0.015` and reduce speed to `0.05` on lines 85 and 95 to improve placement precision.