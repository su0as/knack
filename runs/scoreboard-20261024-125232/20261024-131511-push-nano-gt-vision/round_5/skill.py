# skill module
import math

def run(robot):
    """
    Push the orange puck so that its centre ends up inside the green circle.
    The puck is too wide to grasp, so we push it with the gripper.
    """

    # --------------------------------------------------------------
    # 1. Perceive the scene (guarded perception)
    # --------------------------------------------------------------
    try:
        puck_pose = robot.get_pose('puck')
        target_pose = robot.get_pose('target')
    except Exception as e:                     # PerceptionError or other failure
        robot.log("Perception error: " + str(e))
        return False

    px, py, _ = puck_pose['pos']
    tx, ty, _ = target_pose['pos']

    # --------------------------------------------------------------
    # 2. Quick success test
    # --------------------------------------------------------------
    if math.hypot(tx - px, ty - py) < 0.04:    # target radius
        return True

    # --------------------------------------------------------------
    # 3. Geometry: push direction and side‑on contact point
    # --------------------------------------------------------------
    dx, dy = tx - px, ty - py
    distance = math.hypot(dx, dy)
    ux, uy = dx / distance, dy / distance          # unit push direction

    # offset perpendicular to push direction (side‑on contact)
    side_offset_x = -uy
    side_offset_y = ux
    contact_offset = 0.03 + 0.005                  # puck radius + small gap
    contact_x = px + side_offset_x * contact_offset
    contact_y = py + side_offset_y * contact_offset
    contact_z = 0.015                            # table‑level height

    # --------------------------------------------------------------
    # 4. Workspace safety check for the contact point
    # --------------------------------------------------------------
    if not (0.04 <= contact_x <= 0.32 and
            -0.26 <= contact_y <= 0.26 and
            0.014 <= contact_z <= 0.26):
        robot.log("Contact point outside safe workspace – aborting.")
        return False

    # --------------------------------------------------------------
    # 5. Approach the puck
    # --------------------------------------------------------------
    approach_yaw = math.atan2(uy, ux)
    try:
        robot.move_to(contact_x, contact_y, contact_z,
                      yaw=approach_yaw, speed=0.07)
    except Exception as e:
        robot.log("Approach move failed: " + str(e))
        return False

    # --------------------------------------------------------------
    # 6. Light contact – ensure we are holding the puck
    # --------------------------------------------------------------
    # tiny lateral nudge to improve finger‑puck contact
    robot.move_by(dx=0.001, dy=0, speed=0.07)
    robot.grasp()                                 # close fingers fully
    if robot.holding() is None:
        # deeper downward press to guarantee contact
        robot.move_by(dz=-0.002, speed=0.07)
        if robot.holding() is None:
            robot.log("Failed to acquire contact after press")
            return False

    # --------------------------------------------------------------
    # 7. Push the puck (bounded iterations, safety‑aware distance)
    # --------------------------------------------------------------
    max_pushes = 3
    desired_push = 0.12                           # ≥0.12 m to meet tolerance
    for _ in range(max_pushes):
        # ---- compute safe push distance respecting x‑margin ----
        # remaining x margin in the direction of ux
        if abs(ux) > 1e-6:
            if ux > 0:
                max_x_push = (0.32 - contact_x) / ux
            else:
                max_x_push = (0.04 - contact_x) / ux
        else:
            max_x_push = float('inf')

        # y‑margin check (same logic as before)
        margin_pos = 0.26 - contact_y
        margin_neg = -0.26 - contact_y
        dy_full = uy * desired_push
        if dy_full > margin_pos:                     # would overshoot positive y
            push_distance = margin_pos / uy if abs(uy) > 1e-6 else 0.0
        elif dy_full < margin_neg:                   # would overshoot negative y
            push_distance = margin_neg / uy if abs(uy) > 1e-6 else 0.0
        else:
            push_distance = desired_push

        # cap by the x‑margin and ensure non‑negative
        push_distance = min(push_distance, max_x_push)
        push_distance = max(0.0, push_distance)

        # displacement for this push
        dx_move = ux * push_distance
        dy_move = uy * push_distance
        new_x = contact_x + dx_move

        # final x‑range safety check
        if not (0.04 <= new_x <= 0.32):
            robot.log("Push would exceed x safe range – aborting.")
            break

        # ---- execute the push ----
        try:
            robot.move_by(dx=dx_move, dy=dy_move, dz=0, speed=0.07)
        except Exception as e:
            robot.log("Push move failed: " + str(e))
            break

        # ---- verify new puck pose ----
        try:
            new_pose = robot.get_pose('puck')
        except Exception as e:
            robot.log("Perception error during push: " + str(e))
            break

        # success test
        if math.hypot(new_pose['pos'][0] - tx, new_pose['pos'][1] - ty) < 0.04:
            # release and final verification
            robot.release()
            final = robot.get_pose('puck')
            if math.hypot(final['pos'][0] - tx, final['pos'][1] - ty) < 0.04:
                return True
            else:
                # fell just short – treat as failure but continue cleanup
                break

    # --------------------------------------------------------------
    # 8. Cleanup on any failure – ensure gripper is open
    # --------------------------------------------------------------
    robot.release()
    return False
