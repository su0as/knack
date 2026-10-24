import math

def run(robot):
    # Constants
    CLEARANCE = 0.06          # increased to avoid start collisions
    APPROACH_Z = 0.025        # push height (fingertips at ~0.0125 m)
    SAFE_Z = 0.05             # height for collision‑free approach
    PUSH_SPEED = 0.05
    TRAVEL_SPEED = 0.10
    NUDGE_DIST = 0.01
    MAX_ATTEMPTS = 2

    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    def in_target(puck_pos, target_pos, target_radius):
        return math.hypot(puck_pos[0] - target_pos[0], puck_pos[1] - target_pos[1]) <= target_radius

    def get_poses():
        obs = robot.observe()
        puck = obs["objects"].get("puck")
        target = obs["fixtures"].get("target")
        if not puck or not target:
            return None, None, None, None
        puck_pos = puck["pos"]
        target_pos = target["pos"]
        puck_radius = puck["size"]["radius"]
        target_radius = target["radius"]
        return puck_pos, target_pos, puck_radius, target_radius

    # Initial check
    puck_pos, target_pos, puck_radius, target_radius = get_poses()
    if puck_pos is None:
        return False
    if in_target(puck_pos, target_pos, target_radius):
        return True

    for attempt in range(MAX_ATTEMPTS):
        # Re‑read poses at start of each attempt
        puck_pos, target_pos, puck_radius, target_radius = get_poses()
        if puck_pos is None:
            break

        dx = target_pos[0] - puck_pos[0]
        dy = target_pos[1] - puck_pos[1]
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            return True
        ux, uy = dx / dist, dy / dist
        push_yaw = math.atan2(uy, ux)  # fingers perpendicular to push direction

        # Start position behind puck
        start_x = clamp(puck_pos[0] - ux * (puck_radius + CLEARANCE), 0.04, 0.32)
        start_y = clamp(puck_pos[1] - uy * (puck_radius + CLEARANCE), -0.26, 0.26)

        # Push end position: through puck to target + proportional margin
        margin = 0.02 * (dist / 0.3)
        push_dist = dist + puck_radius + margin
        end_x = clamp(puck_pos[0] + ux * push_dist, 0.04, 0.32)
        end_y = clamp(puck_pos[1] + uy * push_dist, -0.26, 0.26)

        # Nudge end position: a bit further
        nudge_x = clamp(end_x + ux * NUDGE_DIST, 0.04, 0.32)
        nudge_y = clamp(end_y + uy * NUDGE_DIST, -0.26, 0.26)

        # 1. Approach start position at safe height
        try:
            robot.move_to(start_x, start_y, SAFE_Z, speed=TRAVEL_SPEED, yaw=push_yaw)
        except MotionError:
            continue  # try next attempt

        # 2. Lower to push height
        try:
            robot.move_to(start_x, start_y, APPROACH_Z, speed=TRAVEL_SPEED, yaw=push_yaw)
        except MotionError:
            continue

        # 3. Push forward slowly
        try:
            robot.move_to(end_x, end_y, APPROACH_Z, speed=PUSH_SPEED, yaw=push_yaw)
        except MotionError:
            pass  # may have stopped short due to contact; continue to nudge

        # 4. Small nudge to ensure crossing threshold
        try:
            robot.move_to(nudge_x, nudge_y, APPROACH_Z, speed=PUSH_SPEED, yaw=push_yaw)
        except MotionError:
            pass

        # 5. Verify
        robot.wait(0.5)
        puck_pos, target_pos, puck_radius, target_radius = get_poses()
        if puck_pos is None:
            break
        if in_target(puck_pos, target_pos, target_radius):
            return True

    # Final verification after all attempts
    robot.wait(0.5)
    puck_pos, target_pos, puck_radius, target_radius = get_poses()
    if puck_pos and in_target(puck_pos, target_pos, target_radius):
        return True

    return False
