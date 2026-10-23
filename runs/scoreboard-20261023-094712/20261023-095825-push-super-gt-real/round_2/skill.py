import math

def run(robot):
    """
    Push the orange puck so its centre ends inside the green circular zone.
    The puck cannot be grasped, so we approach it from the opposite side of the target,
    move the gripper over the puck, then push forward at table height.
    """
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            obs = robot.observe()
            puck = obs["objects"]["puck"]
            target = obs["fixtures"]["target"]

            puck_pos = puck["pos"]          # [x, y, z]
            target_pos = target["pos"]      # [x, y, 0]
            puck_radius = puck["size"]["radius"]  # assume size dict has radius

            # Vector from puck to target
            dx = target_pos[0] - puck_pos[0]
            dy = target_pos[1] - puck_pos[1]
            dist = math.hypot(dx, dy)
            if dist < 1e-4:  # already on target
                return True
            ux = dx / dist
            uy = dy / dist

            # Stand‑off distance: puck radius + small clearance
            offset = puck_radius + 0.01
            behind_x = puck_pos[0] - offset * ux
            behind_y = puck_pos[1] - offset * uy

            # Heights: high enough to clear puck, then low for pushing
            stand_off_z = 0.05   # tool point height to avoid hitting puck
            push_z = 0.02        # tool point height for contact (fingertips ~0.0075 m)

            # 1. Move to stand‑off point above the puck
            robot.move_to(behind_x, behind_y, stand_off_z, speed=0.15)

            # 2. Lower to pushing height while staying behind the puck
            robot.move_to(behind_x, behind_y, push_z, speed=0.07)

            # 3. Push forward to the target (no extra margin)
            push_dist = dist + offset
            push_x = puck_pos[0] + ux * push_dist
            push_y = puck_pos[1] + uy * push_dist
            robot.move_to(push_x, push_y, push_z, speed=0.07)

            # 4. Lift slightly to avoid dragging the puck back
            robot.move_by(dz=0.02, speed=0.1)

            # 5. Verify success
            obs2 = robot.observe()
            puck_pos2 = obs2["objects"]["puck"]["pos"]
            dx2 = puck_pos2[0] - target_pos[0]
            dy2 = puck_pos2[1] - target_pos[1]
            if math.hypot(dx2, dy2) <= target["radius"]:
                return True

            # If not successful, loop will retry with fresh perception
        except Exception as e:
            robot.log("Exception during push attempt:", e)
            continue

    return False
