**Mode 1: Grasp failure (all seeds)**
- **Episodes:** 8
- **Root cause:** `grasp()` returns `holding: null` every attempt (lines 64, 69). The gripper closes but fails to retain the cube.
- **Fix:** Increase `grasp_offset` from `0.02` to `0.05` in `_pick_and_place` (line 47) to close fingers deeper onto the cube.

**Mode 2: Tray mis‑alignment (seeds 2000‑2003)**
- **Episodes:** 4
- **Root cause:** `place_z = tray_pose['pos'][2] + place_offset` (line 83) uses a fixed `place_offset=0.02`. Perception places the tray top at `z≈0.015`, so the cube lands at `z≈0.035`, above the tray interior and sliding off.
- **Fix:** Set `place_offset = -0.005` to release `0.005 m` below the tray top, letting the cube settle inside.

**Mode 3: Tray mis‑alignment (seeds 2004‑2007)**
- **Episodes:** 4
- **Root cause:** Same `place_offset=0.02` issue, but tray poses have higher `z` (≈0.013–0.014), pushing cubes even higher.
- **Fix:** Same as Mode 2: change `place_offset` to `-0.005` (line 48).