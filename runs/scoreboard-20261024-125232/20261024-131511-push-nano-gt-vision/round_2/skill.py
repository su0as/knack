# skill module
import math

def run(robot):
    """
    Push the orange puck so that its centre ends up inside the green circle.
    The puck is too wide to grasp, so we push it with the gripper.
    """

    # --------------------------------------------------------------
    # 1. Perceive the scene
    # --------------------------------------------------------------
    puck_pose = robot.get_pose('puck')
    target_pose = robot.get_pose('target')
    px, py, pz = puck_pose['pos']
    tx, ty, tz = target_pose['pos']

    # --------------------------------------------------------------
    # 2. Compute geometric data
    # --------------------------------------------------------------
    dx, dy = tx - px, ty - py
    distance = math.hypot(dx, dy)

    # Already inside target?
    if distance < 0.04:          # target radius
        return True

    # Unit push direction
    ux, uy = dx / distance, dy / distance

    # --------------------------------------------------------------
    # 3. Compute a side‑on contact point (avoid head‑on collision)
    # --------------------------------------------------------------
    # offset vector perpendicular to push direction
    side_offset_x = -uy
    side_offset_y = ux
    contact_offset = 0.03 + 0.005          # puck radius + small gap
    contact_x = px + side_offset_x * contact_offset
    contact_y = py + side_offset_y * contact_offset
    contact_z = 0.015                      # table‑level height

    # --------------------------------------------------------------
    # 4. Verify safe workspace
    # --------------------------------------------------------------
    if not (0.04 <= contact_x <= 0.32 and
            -0.26 <= contact_y <= 0.26 and
            0.014 <= contact_z <= 0.26):
        robot.log("Target pose outside safe workspace – aborting.")
        return False

    # --------------------------------------------------------------
    # 5. Approach the puck
    # --------------------------------------------------------------
    # Align closing direction with the push direction (ux, uy)
    approach_yaw = math.atan2(uy, ux)

    robot.move_to(
        contact_x,
        contact_y,
        contact_z,
        yaw=approach_yaw,
        speed=0.07
    )

    # --------------------------------------------------------------
    # 6. Light contact – close fingers just enough to touch
    # --------------------------------------------------------------
    robot.grasp()                     # close to max 5 cm
    if robot.holding() is None:
        # tiny downward press to ensure finger‑puck contact
        robot.move_by(dz=-0.001, speed=0.07)

    # --------------------------------------------------------------
    # 7. Push the puck (up to two iterations)
    # --------------------------------------------------------------
    push_distance = 0.05               # 5 cm push
    pushed = 0
    while pushed < 2:                  # at most two pushes
        try:
            robot.move_by(
                dx=ux * push_distance,
                dy=uy * push_distance,
                dz=0,
                speed=0.07
            )
        except Exception:            # should not happen, but be safe
            robot.log("Push move failed – aborting.")
            break

        # Check new distance to target
        new_pose = robot.get_pose('puck')
        new_dx, new_dy = tx - new_pose['pos'][0], ty - new_pose['pos'][1]
        new_dist = math.hypot(new_dx, new_dy)

        if new_dist < 0.04:           # success
            break

        pushed += 1
        # If still not inside, try another push with same parameters
        # (the next iteration will reuse the same ux, uy)

    # --------------------------------------------------------------
    # 8. Release the gripper
    # --------------------------------------------------------------
    robot.release()

    # --------------------------------------------------------------
    # 9. Final verification (optional but safe)
    # --------------------------------------------------------------
    final_pose = robot.get_pose('puck')
    final_dx, final_dy = tx - final_pose['pos'][0], ty - final_pose['pos'][1]
    if math.hypot(final_dx, final_dy) < 0.04:
        return True
    else:
        # Did not reach the target – treat as failure
        return False
