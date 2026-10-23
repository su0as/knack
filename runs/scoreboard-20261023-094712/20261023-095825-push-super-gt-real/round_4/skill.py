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

            # Extract puck radius (handle dict or list size)
            size = puck["size"]
            if isinstance(size, dict) and "radius" in size:
                puck_radius = size["radius"]
            elif isinstance(size, (list, tuple)) and len(size) > 0:
                puck_radius = size[0] / 2.0
            else:
                puck_radius = 0.02  # fallback

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

            # Heights: high enough to clear puck during approach, low for pushing
            stand_off_z = 0.07   # increased to avoid hitting puck on approach
            push_z = 0.025       # lowered to push close to the table surface

            # 1. Move to stand‑off point above the puck (based on initial observation)
            robot.move_to(behind_x, behind_y, stand_off_z, speed=0.15)

            # 2. Lower to pushing height while staying behind the puck
            robot.move_to(behind_x, behind_y, push_z, speed=0.07)

            # 3. Re‑observe to get latest puck position before pushing
            obs2 = robot.observe()
            puck_pos2 = obs2["objects"]["puck"]["pos"]
            # Re‑compute vector from updated puck position to target
            dx2 = target_pos[0] - puck_pos2[0]
            dy2 = target_pos[1] - puck_pos2[1]
            dist2 = math.hypot(dx2, dy2)
            if dist2 < 1e-4:
                return True
            ux2 = dx2 / dist2
            uy2 = dy2 / dist2

            # Push distance with proportional margin to avoid over/under shoot
            margin = 0.02 * dist2
            if margin < 0.005:
                margin = 0.005
            push_dist = dist2 + offset + margin
            push_x = puck_pos2[0] + ux2 * push_dist
            push_y = puck_pos2[1] + uy2 * push_dist
            robot.move_to(push_x, push_y, push_z, speed=0.07)

            # 4. Lift sufficiently to avoid dragging the puck back
            robot.move_by(dz=0.04, speed=0.1)
            robot.wait(0.1)  # brief settle time

            # 5. Verify success
            obs3 = robot.observe()
            puck_pos3 = obs3["objects"]["puck"]["pos"]
            dx3 = puck_pos3[0] - target_pos[0]
            dy3 = puck_pos3[1] - target_pos[1]
            if math.hypot(dx3, dy3) <= target["radius"]:
                return True

            # If not successful, loop will retry with fresh perception
        except Exception as e:
            robot.log("Exception during push attempt:", e)
            continue

    return False
