# skill module
import math

def run(robot):
    """
    Push the orange puck so that its centre ends up inside the green circle.
    The puck cannot be grasped, so we push it with the gripper.
    """

    # --------------------------------------------------------------
    # 1. Perceive the scene
    # --------------------------------------------------------------
    try:
        puck_pose = robot.get_pose('puck')
        target_pose = robot.get_pose('target')
    except Exception as e:
        robot.log("Perception error: " + str(e))
        return False

    px, py, _ = puck_pose['pos']
    tx, ty, _ = target_pose['pos']

    # --------------------------------------------------------------
    # 2. Quick success test
    # --------------------------------------------------------------
    if math.hypot(tx - px, ty - py) < 0.04:   # target radius
        return True

    # --------------------------------------------------------------
    # 3. Geometry of a side‑on contact point
    # --------------------------------------------------------------
    dx, dy = tx - px, ty - py
    distance = math.hypot(dx, dy)
    ux, uy = dx / distance, dy / distance          # unit push direction

    # offset perpendicular to push direction (side‑on contact)
    side_offset_x = -uy
    side_offset_y = ux
    contact_offset = 0.03 + 0.005                    # puck radius + tiny gap
    contact_x = px + side_offset_x * contact_offset
    contact_y = py + side_offset_y * contact_offset
    contact_z = 0.015                               # table height

    # --------------------------------------------------------------
    # 4. Verify contact point is inside the safe workspace
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
    # 6. Light contact – try to acquire the puck
    # --------------------------------------------------------------
    # tiny lateral nudge
    robot.move_by(dx=0.001, dy=0, speed=0.07)
    robot.grasp()                                     # close fully

    # verify contact; if missing, try a deeper press (max 2 attempts)
    if robot.holding() is None:
        robot.move_by(dz=-0.002, speed=0.07)
        if robot.holding() is None:
            robot.log("Failed to acquire contact after press")
            return False

    # --------------------------------------------------------------
    # 7. Push loop – keep pushing until tolerance reached or margins exhausted
    # --------------------------------------------------------------
    max_pushes = 5
    for _ in range(max_pushes):
        # re‑read current puck pose (may have moved after grasp)
        try:
            cur_pose = robot.get_pose('puck')
        except Exception as e:
            robot.log("Perception error during push: " + str(e))
            break

        cur_x, cur_y, _ = cur_pose['pos']
        cur_dist = math.hypot(tx - cur_x, ty - cur_y)
        if cur_dist < 0.035:                     # already inside target circle
            robot.release()
            return True

        # vector from current puck centre to target
        dx_to = tx - cur_x
        dy_to = ty - cur_y
        ux_to, uy_to = dx_to / cur_dist, dy_to / cur_dist

        # how far do we still need to travel to meet the tolerance?
        needed = cur_dist - 0.035                # excess beyond the 0.035 m radius
        if needed <= 0:
            robot.release()
            return True

        # ---- safety‑margin calculations ----
        # x‑margin in the push direction
        if abs(ux_to) > 1e-6:
            if ux_to > 0:
                max_x_push = (0.32 - contact_x) / ux_to
            else:
                max_x_push = (0.04 - contact_x) / ux_to
        else:
            max_x_push = float('inf')

        # y‑margin in the push direction
        if abs(uy_to) > 1e-6:
            if uy_to > 0:
                max_y_push = (0.26 - contact_y) / uy_to
            else:
                max_y_push = (-0.26 - contact_y) / uy_to
        else:
            max_y_push = float('inf')

        # maximum safe push distance for this iteration
        safe_push = min(max_x_push, max_y_push, needed)
        safe_push = max(1e-5, safe_push)        # avoid zero‑length moves

        # displacement for this push
        dx_move = ux_to * safe_push
        dy_move = uy_to * safe_push

        # final safety check before execution
        new_x = contact_x + dx_move
        new_y = contact_y + dy_move
        if not (0.04 <= new_x <= 0.32 and -0.26 <= new_y <= 0.26):
            robot.log("Push would exit safe workspace – aborting.")
            break

        # ---- execute the push ----
        try:
            robot.move_by(dx=dx_move, dy=dy_move, dz=0, speed=0.07)
        except Exception as e:
            robot.log("Push move failed: " + str(e))
            break

        # after the move, verify the new pose
        try:
            new_pose = robot.get_pose('puck')
        except Exception as e:
            robot.log("Perception error after push: " + str(e))
            break

    # --------------------------------------------------------------
    # 8. Cleanup on any failure – ensure gripper is open
    # --------------------------------------------------------------
    robot.release()
    return False
