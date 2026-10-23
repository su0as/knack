- Round 5 showed two main failure modes: (1) timeouts on the slow absolute `move_to` push (speed 0.02) when the arm traverses long paths or hits joint limits; (2) start positions clamped into workspace walls that exceed the robot's horizontal reach radius (~0.25 m).
- Fixes implemented:
  1. Replaced the absolute push `move_to` with a relative `move_by` along the push direction – avoids coordinate drift, shortens path, and respects the 45 s budget.
  2. Added a reachability check (`is_reachable`) for the start position; if unreachable, iteratively reduce the approach distance until the start is within the reachable radius.
  3. Enforce a 5 cm clearance from workspace bounds *before* clamping, and keep the start position inside the reachable disc.
  4. Reduced push speed to 0.02 m/s (via `move_by`) and limited attempts to 4 to stay within time budget.
  5. Fixed all previously undefined variables (`max_attempts`, `approach_dist`, `local_push_z`, `rotate_vec`, etc.) and added robust puck‑radius extraction.
  6. Added lead‑angle correction for upright puck slide, and increase approach distance when puck is edge‑on or already close to target.
  7. Re‑observe after each push and exit early on success.