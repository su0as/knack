**Mode 1: Premature success log (n=3)**
- **Root cause:** `move_to_pose` returns `True` on `res.get("ok", False)` even when the final z-position is below `SAFE_Z`. The function does not validate the actual z-coordinate before reporting success (lines 25–41).
- **Fix:** Add a z-check after `move_to_pose` returns `True`; if `target_pos[2] < SAFE_Z`, log failure and retry or retreat.

**Mode 2: Grasp succeeds but lift stalls below SAFE_Z (n=2)**
- **Root cause:** After a successful grasp, `move_to_pose` lifts to `SAFE_Z` but the observed cube z remains below threshold. The subsequent nudge (`move_by(dz=0.002)`) is too small to overcome pose error (lines 96–105).
- **Fix:** Increase nudge magnitude to `dz=0.01` or adjust `SAFE_Z` margin to `0.005` to absorb typical motion error.

**Mode 3: Observation gap during retreat (n=2)**
- **Root cause:** `safe_observe` moves the gripper sideways (`dx=0.05`) to unocclude the cube, but this shifts the robot base, causing subsequent `move_to_pose` calls to use stale coordinates, resulting in low lifts (lines 16–19, 63).
- **Fix:** Reset to `home()` before the lift phase, or increase `SAFE_Z` to `0.07` to tolerate positional drift.