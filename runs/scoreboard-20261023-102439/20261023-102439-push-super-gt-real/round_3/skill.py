import math
from collections import deque

def run(robot):
    """Push the orange puck until its centre lies inside the green zone."""
    max_attempts = 5          # how many push cycles we will try
    back_offset = 0.05        # distance behind the puck to start the push (m)
    push_distance = 0.08      # how far we move forward while pushing (m)
    safe_z = 0.02             # safe height for the tool point (m)

    # history of recent puck positions for smoothing (max 3 samples)
    pos_history = deque(maxlen=3)

    for attempt in range(max_attempts):
        # 1️⃣  Get latest noisy observations
        obs = robot.observe()
        puck = obs['objects']['puck']
        target = obs['fixtures']['target']

        # raw puck position
        raw_x, raw_y, _ = puck['pos']
        pos_history.append((raw_x, raw_y))

        # compute smoothed position (average of available samples)
        if pos_history:
            sx = sum(p[0] for p in pos_history)
            sy = sum(p[1] for p in pos_history)
            cnt = len(pos_history)
            puck_x = sx / cnt
            puck_y = sy / cnt
        else:
            puck_x, puck_y = raw_x, raw_y

        # target position
        tgt_x, tgt_y, _ = target['pos']

        # 2️⃣  Already inside the target?
        dx = tgt_x - puck_x
        dy = tgt_y - puck_y
        dist_to_target = math.hypot(dx, dy)
        if dist_to_target <= target['radius']:
            return True
        if dist_to_target < 1e-6:  # avoid division by zero
            return True

        # Unit vector from puck to target (using smoothed puck position)
        ux = dx / dist_to_target
        uy = dy / dist_to_target

        # 3️⃣  Position behind the puck (the "push start")
        approach_x = puck_x - ux * back_offset
        approach_y = puck_y - uy * back_offset

        # 4️⃣  Move to the start pose
        try:
            res = robot.move_to(approach_x, approach_y, safe_z,
                                yaw=math.atan2(uy, ux))
        except Exception:   # MotionError or any unexpected issue
            continue
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

    # Final verification after all attempts (use fresh observation)
    obs = robot.observe()
    puck = obs['objects']['puck']
    target = obs['fixtures']['target']
    px, py, _ = puck['pos']
    tx, ty, _ = target['pos']
    return math.hypot(tx - px, ty - py) <= target['radius']
