# skill module
import math
import numpy as np

def run(robot):
    # ---------- 1. perception ----------
    obs = robot.observe()
    puck = obs["objects"]["puck"]
    target = obs["fixtures"]["target"]
    puck_pos = np.array(puck["pos"], dtype=float)          # centre of puck
    target_pos = np.array(target["pos"][:2], dtype=float)  # (x, y) of zone centre
    target_radius = target["radius"]

    # ---------- 2. approach from above ----------
    # 5 mm clearance above the puck centre avoids side interference
    approach_z = puck_pos[2] + 0.005
    try:
        robot.move_to(puck_pos[0], puck_pos[1], approach_z, speed=0.05)
    except Exception:
        # if unreachable, lower just enough to stay in workspace
        approach_z = max(approach_z, 0.02)
        robot.move_to(puck_pos[0], puck_pos[1], approach_z, speed=0.05)

    # ---------- 3. descend to touch the puck top ----------
    # fingertips are 1.25 cm below the tool point; lower by that amount
    try:
        robot.move_by(dz=-0.0125, speed=0.05)
    except Exception:
        # if blocked, raise a bit and try the descent again
        robot.move_by(dz=0.005, speed=0.05)
        robot.move_by(dz=-0.0125, speed=0.05)

    # ---------- 4. push toward the target ----------
    delta = target_pos - puck_pos[:2]
    dist_to_target = np.linalg.norm(delta)
    # keep pushes small (<1.5 cm) to stay within time & safety limits
    push_step = min(0.015, dist_to_target)
    if push_step > 0:
        direction = delta / dist_to_target
        try:
            robot.move_by(
                dx=direction[0] * push_step,
                dy=direction[1] * push_step,
                speed=0.05
            )
        except Exception:
            # blocked – abort this episode, will be retried next seed
            pass

    # ---------- 5. lift back to approach height ----------
    try:
        robot.move_to(puck_pos[0], puck_pos[1], approach_z, speed=0.05)
    except Exception:
        pass

    # ---------- 6. verify placement ----------
    final_obs = robot.observe()
    final_puck = np.array(final_obs["objects"]["puck"]["pos"], dtype=float)
    final_dist = np.linalg.norm(final_puck[:2] - target_pos)
    if final_dist < target_radius:
        return True

    # ---------- 7. optional corrective push ----------
    # If still outside, try one extra tiny push (≤ 0.005 m)
    if push_step > 0.005:
        corr_step = 0.005
        direction = delta / dist_to_target
        try:
            robot.move_by(
                dx=direction[0] * corr_step,
                dy=direction[1] * corr_step,
                speed=0.05
            )
            # lift again and re‑check
            robot.move_to(puck_pos[0], puck_pos[1], approach_z, speed=0.05)
            final_obs = robot.observe()
            final_puck = np.array(final_obs["objects"]["puck"]["pos"], dtype=float)
            final_dist = np.linalg.norm(final_puck[:2] - target_pos)
            if final_dist < target_radius:
                return True
        except Exception:
            pass

    return False
