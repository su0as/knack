- **Mode 1 (premature release / drift)** – The cube was released before it reached the correct stacked height, so it fell back to the table. Fixed by:
  * Adding a post‑release pose check that the red cube’s centre is at `blue_z + 0.03 m` (within 0.01 m). If not, abort and return False.
  * Keeping the lift‑to‑placement height before releasing and verifying that the gripper is still holding the red cube just before release.
- **Mode 2 (perception mismatch)** – If the colour scan fails or the objects are briefly occluded, `red_name`/`blue_name` can be `None`. Fixed by:
  * Requiring both names to be found and that their `z` positions are ≈ 0.015 m (table height) within 0.02 m; otherwise re‑observe once before aborting.
- **Robustness** – Added explicit `MotionError` catching, a small retry loop for hold verification, and a final pose validation after release. All changes preserve the successful behaviour seen in the other 7 episodes.