**Mode 1: Approach timeout** (2 episodes: 2003, 2004)  
**Root cause:** The descent to push height (line 55) moves at 0.05 m/s. When the puck is far or offset, the arm traverses a long horizontal distance at this slow speed, exceeding the 45 s budget before reaching `z=0.02`.  
**Fix:** Increase the descent speed to `0.15` on line 55, matching the approach speed used earlier.

**Mode 2: Initial approach timeout** (1 episode: 2006)  
**Root cause:** The first `move_to` to the contact point (line 40) also uses the slow 0.05 m/s speed. A distant puck causes a long traverse that times out before the push can begin.  
**Fix:** Raise the speed on line 40 to `0.15` so the arm reaches the contact point promptly.

**Mode 3: Overshoot / instability** (1 episode: 2006)  
**Root cause:** After a successful approach, the final push (line 70) moves at 0.05 m/s to `z=0.02`. The low speed combined with the short push distance can cause the puck to nudge sideways or the arm to overshoot due to residual momentum, leaving the puck off‑target.  
**Fix:** Raise the push speed on line 70 to `0.15` to deliver the push decisively before the arm lifts clear.