# skill module
import math

def run(robot):
    """
    Push the orange puck so that its centre ends up inside the green circle.
    The puck is too wide to grasp, so we push it with the gripper.
    """

    # --------------------------------------------------------------
    # 1. Perceive the scene (with guarded perception)
    # --------------------------------------------------------------
    try:
        puck_pose = robot.get_pose('puck')
        target_pose = robot.get_pose('target')
    except Exception as e:                     # PerceptionError or other failure
        robot.log("Perception error: " + str(e))
        return False

    px, py, pz = puck_pose['pos']
    tx, ty, tz = target_pose['pos']

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
    # 4. Workspace safety check
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
    robot.grasp()                                 # close fingers fully
    if robot.holding() is None:
        # tiny downward press to guarantee finger‑puck contact
        robot.move_by(dz=-0.001, speed=0.07)
        if robot.holding() is None:
            robot.log("Failed to acquire contact after press")
            return False

    # --------------------------------------------------------------
    # 7. Push the puck (up to three iterations, larger distance)
    # --------------------------------------------------------------
    push_distance = 0.12                           # ≥0.12 m to meet tolerance
    max_pushes = 3
    for _ in range(max_pushes):
        try:
            robot.move_by(dx=ux * push_distance,
                          dy=uy * push_distance,
                          dz=0,
                          speed=0.07)
        except Exception as e:
            robot.log("Push move failed: " + str(e))
            break

        # Verify new pose of the puck
        try:
            new_pose = robot.get_pose('puck')
        except Exception as e:
            robot.log("Perception error during push: " + str(e))
            break

        # Check if we are inside the target circle
        if math.hypot(new_pose['pos'][0] - tx, new_pose['pos'][1] - ty) < 0.04:
            # Success path: release and final verification
            robot.release()
            final = robot.get_pose('puck')
            if math.hypot(final['pos'][0] - tx, final['pos'][1] - ty) < 0.04:
                return True
            else:
                # Fell just short – treat as failure but keep cleanup
                break

    # --------------------------------------------------------------
    # 8. Cleanup on any failure – ensure gripper is open
    # --------------------------------------------------------------
    robot.release()
    return False
