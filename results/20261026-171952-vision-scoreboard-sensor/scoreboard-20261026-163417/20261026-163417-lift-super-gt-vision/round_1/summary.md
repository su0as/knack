**Mode 1: yaw argument rejected**  
- **Episodes:** 8 (seed 1000–1007)  
- **Root cause:** `move_to_pose` is defined with parameters `target_pos` and `target_yaw` (line 24), but the call at line 64 passes `yaw=cube_yaw`. The function expects the positional argument `target_yaw`, not the keyword `yaw`.  
- **Fix:** Change line 64 to `if not move_to_pose(approach_pos, cube_yaw, desc="approach"):`.

**Mode 2: insufficient lift height**  
- **Episodes:** All 8 share `red_cube_z=0.0149` vs `required_z=0.065`.  
- **Root cause:** `SAFE_Z = 0.08` (line 6) is set to 8 cm, but the check expects 6.5 cm. The grasp descends to `GRASP_Z = 0.015` (line 7), and lifting to `SAFE_Z` should clear 5 cm. The discrepancy suggests the check logic or `SAFE_Z` value is mismatched with the 5 cm requirement.  
- **Fix:** Set `SAFE_Z = 0.065` on line 6 to meet the 5 cm threshold exactly.