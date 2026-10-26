**Mode 1: Approach timeout (4 episodes, seeds 3000, 3001, 3006, 3007)**
*Root cause:* `try_approach` at line 92 calls `robot.move_to` which stops short when blocked. The code retries fallbacks (lines 104‑111) but the robot repeatedly fails to reach the approach point, exhausting the 70 s budget before all colours are placed.
*Fix:* Reduce `APPROACH_SPEED` (line 23) or increase `FORWARD_OFFSET` (line 15) to give the robot more clearance, or add a maximum‑retry count inside `try_approach` to abort early instead of looping until the time budget ends.

**Mode 2: UnboundLocalError – fallback_offsets missing (2 episodes, seeds 3002, 3005)**
*Root cause:* `fallback_offsets` is defined inside the `try_approach` exception handler (line 88) but referenced later at lines 104 and 120 outside that scope. If the first `try_approach` call succeeds, the variable is never created, causing an `UnboundLocalError` when the fallback loop runs.
*Fix:* Move the `fallback_offsets` definition to the top of the `run` function (before the `while` loop) so it is always available, or duplicate the list at lines 104 and 120 outside the helper.

**Mode 3: Tray approach blocked (2 episodes, seeds 3004, 3005)**
*Root cause:* After a successful grasp, the tray‑approach moves (lines 174‑192) fail because the robot’s end‑effector is obstructed or the tray pose is slightly off. The fallback shifts (LATERAL_FALLBACK, line 19) are attempted but sometimes still blocked, leading to a skip and the colour not being placed.
*Fix:* Lower `release_z_above` (line 157) by a small margin or add a secondary fallback that shifts both x and y simultaneously, increasing the chance of finding a clear path.