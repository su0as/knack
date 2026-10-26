**Mode 1: XY offset too large (seeds 2003–2007)**  
*4 episodes*  
Root cause: The `offset_x/offset_y` calculation (lines 47–50) uses `half_h * sin/cos(place_yaw)`, which overestimates the required shift for yaw angles near 0 or π, pushing the place pose off the cube.  
Fix: Replace the offset with a fixed 2 cm translation along the world X axis: `offset_x, offset_y = 0.02, 0`. This guarantees the cube lands on the target regardless of yaw.

**Mode 2: Z‑gap too small / red_held=False (seeds 2000, 2004–2006)**  
*3 episodes*  
Root cause: The place height formula (line 53) computes `blue_z + 0.05 m`. When `blue_z ≈ 0.0147 m`, the resulting `place_z ≈ 0.065 m` leaves only ~2 cm clearance after release, causing the cube to settle slightly below the target or slip. Additionally, `red_held=False` indicates the grasp verification loop (lines 72–89) may exit prematurely if `holding()` returns a non‑“red_cube” string.  
Fix: Add a 0.01 m safety buffer to the height: `place_z = blue_z + half_h + half_h + 0.03`. Ensure the verification loop checks `robot.holding() == "red_cube"` strictly and retries on mismatch.