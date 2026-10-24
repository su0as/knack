# skill module
import math
import numpy as np

MAX_PUSH_STEPS = 4          # safety cap to stay inside time budget
MAX_PUSH_PER_STEP = 0.025   # 2.5 cm per step (still safe)
CLEARANCE_ABOVE = 0.015     # 1.5 cm clearance to avoid side collisions
MIN_APPROACH_Z = 0.014      # safe workspace lower bound
SLOW_SPEED = 0.05           # m/s, used everywhere


def run(robot):
    # ---------- 1. perception ----------
    obs = robot.observe()
    puck = obs["objects"]["puck"]
    target = obs["fixtures"]["target"]
    puck_pos = np.array(puck["pos"], dtype=float)          # centre of puck
    target_pos = np.array(target["pos"][:2], dtype=float)  # (x, y) of zone centre
    target_radius = target["radius"]

    # If already inside, succeed immediately
    if np.linalg.norm(puck_pos[:2] - target_pos) < target_radius:
        return True

    # ---------- 2. approach from above ----------
    # Use a fixed clearance that is large enough to avoid side collisions
    approach_z = puck_pos[2] + CLEARANCE_ABOVE
    # Clamp to safe workspace limits
    approach_z = max(approach_z, MIN_APPROACH_Z)
    approach_z = min(approach_z, 0.26)  # upper safe bound (unlikely to be hit)

    try:
        robot.move_to(puck_pos[0], puck_pos[1], approach_z, speed=SLOW_SPEED)
    except Exception:
        # If the first height is unreachable, try a slightly higher one
        approach_z = min(approach_z + 0.005, 0.26)
        robot.move_to(puck_pos[0], puck_pos[1], approach_z, speed=SLOW_SPEED)

    # ---------- 3. descend to touch the puck top ----------
    # Fingertips are 1.25 cm below the tool point; lower by that amount
    try:
        robot.move_by(dz=-0.0125, speed=SLOW_SPEED)
    except Exception:
        # Blocked – lift a bit and try again once
        robot.move_by(dz=0.005, speed=SLOW_SPEED)
        robot.move_by(dz=-0.0125, speed=SLOW_SPEED)

    # ---------- 4. iterative pushing ----------
    # We will keep pushing until we are inside the target or we exhaust attempts
    for step in range(MAX_PUSH_STEPS):
        # Re‑observe to get the current puck pose (may have moved)
        obs = robot.observe()
        puck = obs["objects"]["puck"]
        puck_pos = np.array(puck["pos"], dtype=float)
        delta = target_pos - puck_pos[:2]
        remaining_dist = np.linalg.norm(delta)

        if remaining_dist < target_radius:
            break  # success, exit loop

        # Compute a safe push step (never exceed remaining distance)
        push_step = min(MAX_PUSH_PER_STEP, remaining_dist)
        direction = delta / remaining_dist if remaining_dist > 0 else np.zeros(2)

        try:
            robot.move_by(
                dx=direction[0] * push_step,
                dy=direction[1] * push_step,
                speed=SLOW_SPEED
            )
        except Exception:
            # If blocked, abort this episode – the next seed will be tried
            return False

        # After the push, lift back up to approach height to reset for next try
        try:
            robot.move_to(puck_pos[0], puck_pos[1], approach_z, speed=SLOW_SPEED)
        except Exception:
            pass

    # ---------- 5. final verification ----------
    final_obs = robot.observe()
    final_puck = np.array(final_obs["objects"]["puck"]["pos"], dtype=float)
    final_dist = np.linalg.norm(final_puck[:2] - target_pos)

    return final_dist < target_radius
