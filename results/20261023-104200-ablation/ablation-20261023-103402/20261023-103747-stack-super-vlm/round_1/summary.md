**Mode 1: Collision during descent (seed 1002)**
- **Episodes:** 1
- **Root cause:** Line 71 descends to `z=blue_pose["pos"][2]` (center height) without accounting for the cube's physical height. The robot drives into the red cube being held, causing a short.
- **Fix:** Change line 71 `z` to `blue_pose["pos"][2] + 0.03` to stop just above the blue cube surface.

**Mode 2: Insufficient vertical lift (seeds 1003, 1007)**
- **Episodes:** 2
- **Root cause:** Line 75 computes `target_z = blue_pose["pos"][2] + 0.03` for stacking, but the release on line 85 occurs at the held cube's center height (line 31), not the computed stack height. The red cube lands at `z≈0.045` instead of `z≈0.048`.
- **Fix:** Add a lift step after line 85: move to `z=target_z + 0.005` before releasing, ensuring the cube clears the blue cube during release.