**Mode 1: Height shortfall (2 episodes: 2000, 2005)**
- **Root cause:** The `lift_z` calculation at line 25 uses `max(cube_pos[2] + 0.05, 0.065)`. When the cube’s z-coordinate is ≤0.015, the sum falls below 0.065, so the robot lifts to ~0.0643 m, missing the 5 cm requirement.
- **Fix:** Change line 25 to `lift_z = max(cube_pos[2] + 0.05, 0.070)` to guarantee ≥5 cm clearance even for low cubes.

**Mode 2: Perception/pose mismatch (1 episode: 2005)**
- **Root cause:** The initial `move_to` at line 29 targets `cube_pos[2] + 0.10`, but the observed cube pose (z=0.0643) differs from the pre-grasp trajectory, causing the arm to undershoot the lift height.
- **Fix:** Add a perception refresh after `grasp()` (before line 45) and re‑measure `lift_z` to ensure the subsequent lift uses the actual cube height.