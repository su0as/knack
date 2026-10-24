**Mode 1: Grasp succeeds, lift fails (4 episodes: 1000, 1004, 1007)**
- **Root cause:** `move_by(dz=0.05)` lifts from the *grasp_z* (c centre + 0.0125 m), but the required height is cube centre + 0.05 m. With cz ≈ 0.05 m, grasp_z ≈ 0.0625 m; a 0.05 m lift only reaches ≈0.0725 m, missing the 0.065 m target in some poses. Line 41.
- **Fix:** Compute target_z = cz + 0.0125 + 0.05 and `move_to(cx, cy, target_z)` instead of `move_by`.

**Mode 2: Grasp fails due to collision/shortage (3 episodes: 1002, 1003, 1005)**
- **Root cause:** `move_to(..., speed=0.05)` descends to `grasp_z` but stops short (error_m > 0.009). The arm contacts the cube or hits a joint limit before reaching the planned height. Lines 30, 33.
- **Fix:** Reduce approach_z by 0.005 m (e.g., `approach_z = grasp_z + 0.025`) to give more clearance, or add a collision-check step before the slow descent.

**Mode 3: Premature release (2 episodes: 1001, 1005)**
- **Root cause:** `release()` is called immediately after `holding()` returns true (lines 48, 54), before the 5 cm lift completes. The gripper opens while the cube is still low.
- **Fix:** Move the `release()` call to after the verification block (after line 45) or remove it entirely if the task ends at lift.