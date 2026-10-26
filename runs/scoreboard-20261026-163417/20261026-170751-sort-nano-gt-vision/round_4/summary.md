**Modes (count / root cause / fix)**

1. **Grasp failure loop** (12 seeds).  
   *Root*: `grasp()` repeatedly fails; `MAX_GRASP_RETRIES=2` is too low, causing early skip.  
   *Fix*: Increase `MAX_GRASP_RETRIES` to 5 and add a small lift (`robot.move_to(..., RELEASE_Z_ABOVE)`) before retry.

2. **Approach blocked by contact/joint limits** (9 seeds).  
   *Root*: `try_approach` falls back through 8 offsets but all stay inside `SAFE_X/Y_MAX=0.32`. Targets near the boundary (e.g. `0.320`) trigger `MotionError` (seed 4003 line 54) or stop short (seeds 4001/4005).  
   *Fix*: Expand `SAFE_X_MAX` to `0.35` and add a diagonal fallback `(-LATERAL_FALLBACK, -LATERAL_FALLBACK)` before giving up.

3. **Tray approach timeout** (2 seeds).  
   *Root*: `EpisodeTimeout` after 35 fallback attempts; fallback offsets exhaust without clearing occlusion.  
   *Fix*: Reduce `MAX_ATTEMPTS` to 20 or add a “lift‑and‑retry” step after 5 fallbacks.

4. **Cube lost / visibility loss** (3 seeds).  
   *Root*: `observe()` returns `not_visible` for the blue cube; loop spins 30 attempts with no progress.  
   *Fix*: Break loop and log “cube lost” after 3 consecutive invisibility frames.