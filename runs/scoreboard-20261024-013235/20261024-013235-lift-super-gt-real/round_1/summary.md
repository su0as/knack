**Mode 1: Insufficient lift height** (5 episodes: 1000, 1001, 1002, 1003, 1005)
*Root cause:* The lift target `cz + 0.05` uses the cube centre z from the *grasp* observation. Due to sensor noise or approach error, the actual cube centre is often ~0.014 m, making `target_z ≈ 0.064 m`, just below the 0.065 m threshold (lines 61‑62).
*Fix:* After a successful grasp, re‑observe the cube pose and use that `cz` for the lift target (after line 42).

**Mode 2: Grasp on edge/collision** (2 episodes: 1004, 1007)
*Root cause:* The robot descends to `cz` (line 32) but the cube is near a table edge or another object. The grasp closes but does not secure a stable lift, causing the cube to slide down during the lift phase (lines 38‑48).
*Fix:* Add a pre‑grasp check that the approach point has `cz > 0.02 m` and no nearby obstacles; if failed, increase `approach_z` by 0.01 m (line 23) before retrying.

**Mode 3: Safety clamp activation** (2 episodes: 1004, 1007)
*Root cause:* Physical contact with the environment triggers the safety clamp, preventing full lift (lines 66‑69). The code returns `False` without retrying.
*Fix:* On clamp detection, command a small retreat `move_by(dz=0.02)` then re‑attempt the lift from the new pose rather than aborting.