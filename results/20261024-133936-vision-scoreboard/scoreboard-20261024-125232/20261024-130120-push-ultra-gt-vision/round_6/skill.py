import math

def run(robot):
    # Constants
    CLEARANCE = 0.06          # keep start position clear of puck silhouette
    APPROACH_Z = 0.025        # push height (fingertips ~0.0125 m above table)
    SAFE_Z = 0.05             # collision-free approach height
    TRAVEL_SPEED = 0.10
    PUSH_SPEED = 0.05
    NUDGE_DIST = 0.08         # increased to overcome friction/latency
    MAX_ATTEMPTS = 3
    POSE_RETRIES = 3
    POSE_RETRY_WAIT = 0.2
    REACH_LIMIT = 0.251       # arm wrist reach limit (x)

    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    def clamp_x(v):
        return clamp(v, 0.04, REACH_LIMIT)

    def clamp_y(v):
        return clamp(v, -0.26, 0.26)

    def in_target(puck_pos, target_pos, target_radius):
        return math.hypot(puck_pos[0] - target_pos[0], puck_pos[1] - target_pos[1]) <= target_radius

    def get_poses():
        """Return (puck_pos, target_pos, puck_radius, target_radius) or (None,)*4."""
        obs = robot.observe()
        robot.wait(0.1)  # ensure fresh data
        puck = obs["objects"].get("puck")
        target = obs["fixtures"].get("target")
        if not puck or not target:
            return None, None, None, None
        puck_pos = puck["pos"]
        target_pos = target["pos"]
        puck_radius = puck["size"]["radius"]
        target_radius = target["radius"]
        return puck_pos, target_pos, puck_radius, target_radius

    # Initial pose acquisition with retries
    puck_pos = target_pos = puck_radius = target_radius = None
    for _ in range(POSE_RETRIES):
        puck_pos, target_pos, puck_radius, target_radius = get_poses()
        if puck_pos is not None:
            break
        robot.wait(POSE_RETRY_WAIT)
    if puck_pos is None:
        return False

    if in_target(puck_pos, target_pos, target_radius):
        return True

    for attempt in range(MAX_ATTEMPTS):
        # Re-read poses at start of each attempt (with retries)
        last_puck_radius = None
        for _ in range(POSE_RETRIES):
            puck_pos, target_pos, puck_radius, target_radius = get_poses()
            if puck_pos is not None:
                if last_puck_radius is not None and abs(puck_radius - last_puck_radius) > 0.02:
                    robot.log("Warning: puck radius changed significantly", last_puck_radius, puck_radius)
                break
            robot.wait(POSE_RETRY_WAIT)
            last_puck_radius = puck_radius
        if puck_pos is None:
            continue

        dx = target_pos[0] - puck_pos[0]
        dy = target_pos[1] - puck_pos[1]
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            return True
        ux, uy = dx / dist, dy / dist
        push_yaw = math.atan2(uy, ux)  # fingers parallel to push direction (as in round 4)

        # Start position behind puck (clamped to reachable workspace)
        start_x = clamp(puck_pos[0] - ux * (puck_radius + CLEARANCE), 0.04, 0.25)
        start_y = clamp(puck_pos[1] - uy * (puck_radius + CLEARANCE), -0.26, 0.26)

        # Desired push distance: dist + NUDGE_DIST
        push_dist = dist + NUDGE_DIST

        # Cap push_dist by reach limits with 1 cm safety margin
        max_push_dist = float('inf')
        if ux > 0:
            max_push_dist = min(max_push_dist, (REACH_LIMIT - 0.01 - puck_pos[0]) / ux)
        elif ux < 0:
            max_push_dist = min(max_push_dist, (0.04 + 0.01 - puck_pos[0]) / ux)
        if uy > 0:
            max_push_dist = min(max_push_dist, (0.26 - 0.01 - puck_pos[1]) / uy)
        elif uy < 0:
            max_push_dist = min(max_push_dist, (-0.26 + 0.01 - puck_pos[1]) / uy)

        push_dist = min(push_dist, max_push_dist)
        if push_dist < 0:
            push_dist = 0

        end_x = clamp_x(puck_pos[0] + ux * push_dist)
        end_y = clamp_y(puck_pos[1] + uy * push_dist)

        # Nudge position: a bit further
        nudge_x = clamp_x(end_x + ux * NUDGE_DIST)
        nudge_y = clamp_y(end_y + uy * NUDGE_DIST)

        # 1. Approach start position at safe height
        try:
            robot.move_to(start_x, start_y, SAFE_Z, speed=TRAVEL_SPEED, yaw=push_yaw)
        except robot.MotionError:
            continue

        # 2. Lower to push height
        try:
            robot.move_to(start_x, start_y, APPROACH_Z, speed=TRAVEL_SPEED, yaw=push_yaw)
        except robot.MotionError:
            continue

        # 3. Push forward slowly
        try:
            robot.move_to(end_x, end_y, APPROACH_Z, speed=PUSH_SPEED, yaw=push_yaw)
        except robot.MotionError:
            pass  # may have stopped short due to contact; continue to nudge

        # 4. Small nudge to ensure crossing threshold
        try:
            robot.move_to(nudge_x, nudge_y, APPROACH_Z, speed=PUSH_SPEED, yaw=push_yaw)
        except robot.MotionError:
            pass

        # 5. Verify with re-observation
        robot.wait(0.5)
        puck_pos, target_pos, puck_radius, target_radius = get_poses()
        if puck_pos is not None and in_target(puck_pos, target_pos, target_radius):
            return True

    # Final verification after all attempts
    robot.wait(0.5)
    puck_pos, target_pos, puck_radius, target_radius = get_poses()
    if puck_pos is not None and in_target(puck_pos, target_pos, target_radius):
        return True

    return False
