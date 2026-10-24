**Mode 1: NameError in _pick_and_place (5001, 5002, 5003, 5004, 5005, 5006)**
- **Episodes:** 6
- **Root cause:** Line 91/92 reference `cube_name` which is out of scope; the function receives `cube_pose` but the trace shows the variable name was never bound in that context.
- **Fix:** Rename the loop variable in `run` from `cube_name` to `cube` and pass `cube` to `_pick_and_place`, or add `cube_name = cube_name` at the start of the function.

**Mode 2: Perception/tray mismatch (5000, 5007)**
- **Episodes:** 2
- **Root cause:** `colour_to_tray` mapping (line 16‑17) uses `fix['color']` from tray fixtures. If tray colour labels differ from cube colour strings, `tray_name` becomes `None` and the cube is skipped, yet logs show placement attempts, indicating a logic gap between mapping and execution.
- **Fix:** Add a debug log `robot.log(f"Mapping {colour} -> {tray_name}")` before the pick loop to verify mappings match observed colours.

**Mode 3: Grasp failure despite pose success (5000‑5006)**
- **Episodes:** 6
- **Root cause:** `robot.grasp()` returns `holding: null` (lines 60‑62), meaning the hand closed but did not capture the cube, likely due to pose offset or slip.
- **Fix:** Increase `grasp_offset` from 0.02 to 0.05 (line 44) to lower the grasp point, or add a pre‑grasp `robot.open()` to ensure clean closure.