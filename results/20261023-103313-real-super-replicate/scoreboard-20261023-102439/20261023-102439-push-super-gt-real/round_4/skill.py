import math

def run(robot):
    """Push the orange puck until its centre lies inside the green zone."""
    max_attempts = 6          # allow a few extra tries
    back_offset = 0.02        # distance behind the puck to start the push (m)
    push_distance = 0.04      # normal push distance (m)
    micro_push_factor = 0.5   # fraction of push_distance for the final micro‑push
    safe_z = 0.02             # safe height for the tool point (m)

    for attempt in range(max_attempts):
        # 1️⃣  Get latest noisy observations
        obs = robot.observe()
        puck = obs['objects']['puck']
        target = obs['fixtures']['target']

        px, py, _ = puck['pos']
        tx, ty, _ = target['pos']

        # 2️⃣  Already inside the target?
        dx = tx - px
        dy = ty - py
        dist_to_target = math.hypot(dx, dy)
        if dist_to_target <= target['radius']:
            return True

        # Avoid division by zero if puck and target coincide (unlikely but safe)
        if dist_to_target < 1e-6:
            return True

        # Unit vector from puck to target
        ux = dx / dist_to_target
        uy = dy / dist_to_target

        # 3️⃣  Position behind the puck (the "push start")
        approach_x = px - ux * back_offset
        approach_y = py - uy * back_offset

        # 4️⃣  Move to the start pose
        try:
            res = robot.move_to(approach_x, approach_y, safe_z,
                                yaw=math.atan2(uy, ux))
        except Exception:
            continue          # try again next attempt
        if not res['ok']:
            continue

        # 5️⃣  Push forward
        push_x = approach_x + ux * push_distance
        push_y = approach_y + uy * push_distance
        try:
            res2 = robot.move_to(push_x, push_y, safe_z,
                                 yaw=math.atan2(uy, ux))
        except Exception:
            continue
        if not res2['ok']:
            continue

        # 6️⃣  Let the puck settle after the push
        robot.wait(0.2)

    # After the main loop, try one final micro‑push if still outside
    obs = robot.observe()
    puck = obs['objects']['puck']
    target = obs['fixtures']['target']
    px, py, _ = puck['pos']
    tx, ty, _ = target['pos']
    dx = tx - px
    dy = ty - py
    dist_to_target = math.hypot(dx, dy)
    if dist_to_target <= target['radius']:
        return True
    if dist_to_target < 1e-6:
        return True

    ux = dx / dist_to_target
    uy = dy / dist_to_target

    # micro‑push: same approach point, shorter push
    approach_x = px - ux * back_offset
    approach_y = py - uy * back_offset
    micro_push = push_distance * micro_push_factor
    push_x = approach_x + ux * micro_push
    push_y = approach_y + uy * micro_push

    try:
        res = robot.move_to(approach_x, approach_y, safe_z,
                            yaw=math.atan2(uy, ux))
    except Exception:
        return False
    if not res['ok']:
        return False

    try:
        res2 = robot.move_to(push_x, push_y, safe_z,
                             yaw=math.atan2(uy, ux))
    except Exception:
        return False
    if not res2['ok']:
        return False

    robot.wait(0.2)

    # Final verification
    obs = robot.observe()
    puck = obs['objects']['puck']
    px, py, _ = puck['pos']
    tx, ty, _ = target['pos']
    return math.hypot(tx - px, ty - py) <= target['radius']
