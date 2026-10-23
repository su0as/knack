**Mode 1: Placement collision (1 episode)**
*Episodes: 3000*
*Root cause:* Line 69 `move_to(tx, ty, place_z)` failed due to contact/joint limit when lowering onto the tray.
*Fix:* Raise `place_z` by 0.01m to give clearance, or adjust tray height `tz` in observation.

**Mode 2: Grasp loss during transfer (3 episodes)**
*Episodes: 3001, 3003, 3004*
*Root cause:* Lines 56–65. The robot moves above the tray (line 57) and descends (line 69) while holding, but the trajectory causes the gripper to collide or lose contact, triggering the "Lost grasp" log.
*Fix:* Insert a `robot.move_by(dz=0.02, speed=0.05)` ascent after line 57 to clear the tray edge before descending to `place_z`.

**Mode 3: Grasp detection failure (2 episodes)**
*Episodes: 3006, 3007*
*Root cause:* Lines 38–47. The grasp loop retries by lifting `dz=0.01`, but the initial approach or cube pose may be outside the sensor’s reliable grasp zone, causing repeated failures.
*Fix:* Increase retry lift to `dz=0.02` and add a pre-grasp `robot.move_to(cx, cy, above_z, speed=0.1)` to ensure stable alignment before closure.