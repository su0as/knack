**Mode 1: Clamped push too short** (3 episodes: 5000, 5003, 5004)  
*Root cause:* The push point is clamped to the safe rectangle (lines 52‑53), which can shift it toward the centre, reducing the effective push distance. When the clamped push point is too close to the approach point, the puck receives insufficient impulse to reach the target radius.  
*Fix:* Extend the safe rectangle margins or add a minimum push‑distance guard after clamping (e.g., if `push_dist < 0.02` nudge `push_x` further outward).

**Mode 2: Approach‑push alignment lost** (2 episodes: 5000, 5003)  
*Root cause:* After clamping, the approach and push points diverge such that the computed `push_yaw` (line 63) no longer aligns with the intended push direction, causing the robot to veer off‑course.  
*Fix:* Re‑compute `push_yaw` using the original (unclamped) direction vector `(ux, uy)` instead of the clamped delta (line 56‑63).

**Mode 3: Rare; all other failures fall within Mode 1 or 2.**