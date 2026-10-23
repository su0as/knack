import math

def run(robot):
    """Stack the red cube on top of the blue cube."""
    try:
        # Start from a known safe pose
        robot.home()

        # Observe the scene to get current poses
        obs = robot.observe()
        red_pose = obs['objects']['red_cube']
        blue_pose = obs['objects']['blue_cube']

        def grasp_cube(pose, desc=""):
            """Attempt to grasp a cube given its pose dictionary."""
            # Position of the cube centre
            cx, cy, cz = pose['pos']
            yaw = pose['yaw']

            # Safety offset above the cube for approach
            approach_z = max(cz + 0.10, 0.10)  # at least 10 cm high
            # Approach from above
            robot.move_to(cx, cy, approach_z, yaw=yaw, speed=0.15)

            # Descend to a point where the fingertips can close around the middle
            # Fingertips sit ~1.25 cm below the tool point; we aim for the cube centre.
            grasp_z = cz + 0.02  # a little above centre to avoid hitting the table
            robot.move_to(cx, cy, grasp_z, yaw=yaw, speed=0.05)

            # Close the fingers
            if not robot.grasp():
                # If grasp failed, retreat and try once more
                robot.move_by(dz=0.05, speed=0.05)
                if not robot.grasp():
                    robot.log(f"Failed to grasp {desc}")
                    return False
            robot.log(f"Grasped {desc}")
            # Lift the cube clear of the table
            robot.move_by(dz=0.10, speed=0.10)
            return True

        # --- Grasp the red cube ---
        if not grasp_cube(red_pose, "red cube"):
            return False

        # --- Move above the blue cube ---
        bx, by, bz = blue_pose['pos']
        robot.move_to(bx, by, 0.10, yaw=None, speed=0.15)  # travel height

        # --- Lower to stacking height ---
        # Desired centre height of the red cube = blue centre + cube height (0.03 m)
        target_z = bz + 0.03
        robot.move_to(bx, by, target_z, yaw=None, speed=0.05)

        # Release the red cube onto the blue one
        robot.release()
        robot.log("Released red cube onto blue cube")

        # Retreat to a safe height
        robot.move_by(dz=0.10, speed=0.10)

        # Optional: return home
        robot.home()
        return True

    except Exception as e:
        # Unexpected errors – log and fail safely
        robot.log(f"Exception: {e}")
        try:
            robot.home()
        except Exception:
            pass
        return False
