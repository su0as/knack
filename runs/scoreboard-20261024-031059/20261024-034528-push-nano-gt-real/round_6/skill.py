# skill module
import math
import numpy as np

# ---------- configuration ----------
MAX_PUSH_ATTEMPTS = 8          # total pushes we will try
MAX_PUSH_PER_STEP = 0.010      # 1.0 cm per step – fits the narrow corridor
CLEARANCE_ABOVE = 0.045        # 4.5 cm clearance to avoid side collisions
MIN_APPROACH_Z = 0.014         # lowest safe height
SLOW_SPEED = 0.05              # m/s, used everywhere

def run(robot):
    # ---------- 1. initial perception ----------
    obs = robot.observe()
    puck = obs["objects"]["puck"]
    target = obs["fixtures"]["target"]
    puck_pos = np.array(puck["pos"], dtype=float)          # centre of puck
    target_pos = np.array(target["pos"][:2], dtype=float)  # (x, y) of zone centre
    target_radius = target["radius"]

    # If puck already inside the target, we are done
    if np.linalg.norm(puck_pos[:2] - target_pos) < target_radius:
        return True

    # ---------- 2. iterative pushing ----------
    for _ in range(MAX_PUSH_ATTEMPTS):
        # Re‑observe to get the current puck pose (it may have moved)
        obs = robot.observe()
        puck = obs["objects"]["puck"]
        puck_pos = np.array(puck["pos"], dtype=float)
        target_pos = np.array(obs["fixtures"]["target"]["pos"][:2], dtype=float)
        target_radius = obs["fixtures"]["target"]["radius"]

        # Success check after re‑observation
        if np.linalg.norm(puck_pos[:2] - target_pos) < target_radius:
            break

        # ----- compute a safe approach pose -----
        delta_xy = target_pos - puck_pos[:2]
        remaining_xy = np.linalg.norm(delta_xy)
        if remaining_xy > 1e-6:
            offset_dir = delta_xy / remaining_xy
            offset = 0.02 * offset_dir               # ~2 cm safe margin
        else:
            offset_dir = np.array([1.0, 0.0])
            offset = np.array([0.02, 0.0])

        approach_xy = puck_pos[:2] + offset
        approach_z = puck_pos[2] + CLEARANCE_ABOVE
        approach_z = max(approach_z, MIN_APPROACH_Z)
        approach_z = min(approach_z, 0.26)

        # ----- retry moving to the approach pose (up to 3 attempts) -----
        for retry in range(3):
            try:
                robot.move_to(approach_xy[0], approach_xy[1], approach_z,
                              speed=SLOW_SPEED)
                break
            except Exception:
                # lift a little and try again
                approach_z = min(approach_z + 0.005, 0.26)
                robot.move_to(approach_xy[0], approach_xy[1], approach_z,
                              speed=SLOW_SPEED)

        # ----- descend to touch the puck top -----
        for _ in range(2):
            try:
                robot.move_by(dz=-0.0125, speed=SLOW_SPEED)
                break
            except Exception:
                robot.move_by(dz=0.005, speed=SLOW_SPEED)
                robot.move_by(dz=-0.0125, speed=SLOW_SPEED)

        # Lift a bit higher to avoid collision on the next descent
        approach_z = min(approach_z + 0.01, 0.26)

        # ----- compute push step -----
        delta = target_pos - puck_pos[:2]
        dist = np.linalg.norm(delta)
        if dist < target_radius:
            break
        push_step = min(MAX_PUSH_PER_STEP, dist)
        direction = delta / dist

        # ----- attempt the push -----
        try:
            robot.move_by(
                dx=direction[0] * push_step,
                dy=direction[1] * push_step,
                speed=SLOW_SPEED
            )
        except Exception:
            # If blocked, lift back to the safe approach height and continue
            try:
                robot.move_to(puck_pos[0], puck_pos[1], approach_z,
                              speed=SLOW_SPEED)
            except Exception:
                pass
            continue   # try the next push attempt

        # After a successful push, lift back up to the safe height
        try:
            robot.move_to(puck_pos[0], puck_pos[1], approach_z,
                          speed=SLOW_SPEED)
        except Exception:
            pass

    # ---------- 3. final verification ----------
    final_obs = robot.observe()
    final_puck = np.array(final_obs["objects"]["puck"]["pos"], dtype=float)
    final_dist = np.linalg.norm(final_puck[:2] - target_pos)

    return final_dist < target_radius
