**Modes (count / root cause / fix)**

1. **Perception loss / occlusions** (3 episodes: 3005, 3006, 3007)  
   *Root*: `get_pose('puck')` fails or returns None during the push loop (skill.py line 92‑95). Puck leaves view or is occluded.  
   *Fix*: Add a visibility check before each push; if puck is lost, abort and restart from the last known pose rather than continuing blindly.

2. **Gripper contact failure** (3 episodes: 3000, 3002, 3003)  
   *Root*: `grasp()` does not establish holding (lines 67‑73). Fingers slip or puck is too wide for a secure grip, so the subsequent `move_by` slides without pushing.  
   *Fix*: Replace the full‑close `grasp()` with a light `touch()` or `approach()` that sets fingers to a minimal opening (e.g., 0.01 m) before the press, ensuring contact without clamping.

3. **Workspace‑safety violation** (3 episodes: 3004, 3006, 3007)  
   *Root*: `move_by` pushes the puck beyond the allowed y‑range [-0.26, 0.26] (skill.py line 47‑49, 82). Target pose or push vector exceeds limits.  
   *Fix*: Clamp the push vector’s y‑component to `max(±0.26 – contact_y)` before `move_by`, or abort if the required displacement would breach the workspace.