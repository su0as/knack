**Mode 1: Premature release & drift**
- **Episodes:** 1000 (1/8)
- **Root cause:** Line 45 returns `False` on motion error, but the trace shows `release()` at t=4.56 after a successful grasp. The robot releases at `safe_z` (line 72) then lifts away (trace t=5.56), dropping the cube before stacking. The `z_gap=0.0` confirms no lift occurred.
- **Fix:** Add a lift check after `release()` (line 92). If `robot.holding() != red_name`, retry the approach or log "drop detected" and return `False`.

**Mode 2: Perception mismatch**
- **Episodes:** 1001–1007 (7/8)
- **Root cause:** Lines 17–21 scan `obs["objects"]` for colors. If the red/blue cubes are occluded or mislabeled, `red_name` or `blue_name` stays `None`, triggering the early exit at line 25. Successful episodes likely had visible cubes; failures had hidden or swapped colors.
- **Fix:** Before grasping, verify `red_name` and `blue_name` are not `None` and that their `z` positions are within `0.02` of each other. If not, re-observed or abort.