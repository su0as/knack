**Mode 1: XY offset + early release** (3 episodes: 3001, 3002, 3005)  
*Root cause:* The arm moves to the blue cube’s initial XY, but the cube shifts during the lift. Release occurs at `release()` (line 118) without re-checking XY alignment, causing the cube to land off‑target.  
*Fix:* After `robot.move_to(b_x, b_y, place_center_z, ...)` (line 105), add a verification step: `if robot.holding() != red_name: robot.log("lost grip"); return False` and only then release. This ensures the cube is still held and XY‑aligned before letting go.

**Mode 2: Z‑height error** (2 episodes: 3006, 3007 – actually successes; 3004 borderline)  
*Root cause:* `place_center_z = b_z + 0.03` (line 88) assumes a fixed blue‑cube height. When `blue_z` deviates from 0.015 m (e.g., 0.0148 m), the target `place_center_z` is slightly off, and the final pose check (line 125) tolerates ±0.015 m, which can be exceeded.  
*Fix:* Compute `place_center_z` dynamically from the fresh blue‑cube pose observed just before placement (line 73‑86) rather than reusing the initial `blue_z`. Use `place_center_z = b_z + 0.03` with `b_z` from `blue_pose2`.