import math

def run(robot):
    """
    Push the orange puck until its centre lies inside the green target zone.
    The puck is too wide to grasp, so we push it by approaching from behind
    and moving the gripper forward while keeping contact with the puck.
    """
    max_attempts = 5
    approach_offset = 0.04   # distance behind puck to start push (m)
    push_speed = 0.08        # slow speed while in contact
    travel_speed = 0.15      # normal speed for repositioning
    lift_height = 0.05       # safe height above table (m)
    contact_height = 0.02    # height where finger pads touch puck (~mid-height)

    for attempt in range(max_attempts):
        # 1. Get latest poses (noisy, fresh each call)
        obs = robot.observe()
        puck = obs["objects"]["puck"]
        target = obs["fixtures"]["target"]

        puck_pos = puck["pos"]
        target_pos = target["pos"]

        # 2. Compute push direction (from puck to target)
        dx = target_pos[0] - puck_pos[0]
        dy = target_pos[1] - puck_pos[1]
        dist_xy = math.hypot(dx, dy)
        if dist_xy < 1e-4:  # already on top of target – consider done
            return True
        dir_x = dx / dist_xy
        dir_y = dy / dist_xy

        # 3. Choose a point behind the puck to start the push
        behind_x = puck_pos[0] - dir_x * approach_offset
        behind_y = puck_pos[1] - dir_y * approach_offset

        # 4. Move to behind puck at a safe height
        try:
            robot.move_to(behind_x, behind_y, lift_height, speed=travel_speed)
        except Exception:
            # If unreachable, try a slightly higher lift
            robot.move_to(behind_x, behind_y, lift_height + 0.02, speed=travel_speed)

        # 5. Lower to contact height (still behind puck)
        try:
            robot.move_to(behind_x, behind_y, contact_height, speed=push_speed)
        except Exception:
            # If we hit something, retreat and retry this attempt
            robot.move_to(behind_x, behind_y, lift_height, speed=travel_speed)
            continue

        # 6. Push forward: move along the direction while staying at contact height
        push_distance = dist_xy + approach_offset  # go a bit past the target to ensure contact
        push_x = behind_x + dir_x * push_distance
        push_y = behind_y + dir_y * push_distance
        try:
            robot.move_to(push_x, push_y, contact_height, speed=push_speed)
        except Exception:
            # Blocked during push – abort this attempt and retry from a new pose
            robot.move_to(behind_x, behind_y, lift_height, speed=travel_speed)
            continue

        # 7. Lift away to avoid dragging the puck back
        robot.move_to(push_x, push_y, lift_height, speed=travel_speed)

        # 8. Check if puck is now inside the target zone
        obs_after = robot.observe()
        puck_after = obs_after["objects"]["puck"]["pos"]
        dx_err = puck_after[0] - target_pos[0]
        dy_err = puck_after[1] - target_pos[1]
        err_dist = math.hypot(dx_err, dy_err)
        if err_dist <= target["radius"]:
            return True  # success

        # If not yet inside, loop again (will re-perceive and retry)

    # Exhausted attempts – give up
    return False
