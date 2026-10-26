**Mode 1: Grasp failure (62% of seeds)**
- **Episodes:** 2000–2007 (all 8)
- **Root cause:** `robot.grasp()` returns `False` at line 93. The contact pose (line 63) places the hand at `z ≈ 0.014–0.017`, but the puck radius estimation falls back to `0.03 m` (line 60). The resulting contact position is too high/offset, preventing finger closure.
- **Fix:** Reduce `contact_offset` from `0.04` to `0.01` (line 62) so the contact pose sits lower on the puck, increasing contact probability.

**Mode 2: Push undershoot (remaining seeds)**
- **Episodes:** none fully successful; all stop at `puck_to_target_xy ≈ 0.11` (line 127–128) while tolerance is `0.035`.
- **Root cause:** Push distance is `0.95 * push_dist_norm` (line 104). The norm is computed from perceived positions (line 44), but perception error (median 2–8 mm) combined with the 95% fraction leaves the puck consistently short of the `0.035` radius zone.
- **Fix:** Increase push fraction to `1.0` (line 104) or add a second small push after release if the first undershoots.