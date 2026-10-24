**Mode 1: Premature lift (n=2)**
*Episodes 2004, 2005.* The robot lifts before the cube clears the table. In seed 2004 the lift target `lift_z=0.060` m is below the 5 cm check (line 59). In seed 2005 the cube never rises (final z = 0.015 m) because the grasp was released early (line 36) after a failed lift attempt (line 54).
*Root cause:* Lift height insufficient or released before verification.
*Fix:* Ensure `lift_z` uses the 0.07 m offset (line 21) and add a post‑grasp height check before release (after line 42).

**Mode 2: Grasp/positioning failure (n=2)**
*Episodes 2005, 2006/2007 (edge).* Seed 2005 misses the cube entirely during approach; seed 2006/2007 succeed but show the mode is sensitive to initial pose. The code retries on motion error (line 27) but may exhaust attempts if the cube pose is consistently mis‑estimated.
*Root cause:* Observation or motion failure not caught/retrying.
*Fix:* Increase `max_attempts` to 5 and add a debug log when `cube_info` is missing to diagnose pose estimation loss.