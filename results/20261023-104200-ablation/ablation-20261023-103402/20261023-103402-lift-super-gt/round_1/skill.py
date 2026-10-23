import math

def run(robot):
    """
    Pick up the red cube and hold it at least 5 cm above the table.
    Returns True if the maneuver appears successful, False otherwise.
    """
    try:
        # 1. Observe the scene to get the red cube's pose
        obs = robot.observe()
        cube = obs["objects"]["red_cube"]
        cx, cy, cz = cube["pos"]          # centre of the cube
        cyaw = cube["yaw"]                # orientation (used to align fingers)

        # 2. Define target heights relative to the cube centre
        #    Grasp: a little above the centre so the finger pads close around the middle
        grasp_z = cz + 0.02               # 2 cm above centre → finger pads ~0.5 cm below centre
        #    Lift: high enough to be safely >5 cm above the table (table at z=0)
        lift_z = cz + 0.07                # 7 cm above centre → ~8.5 cm above table
        #    Travel height: comfortably above the cube to avoid collisions
        travel_z = cz + 0.12              # 12 cm above centre

        # 3. Move to a safe pose above the cube
        robot.move_to(cx, cy, travel_z, yaw=cyaw, speed=0.2)

        # 4. Descend to the grasp position (slow for precision)
        robot.move_to(cx, cy, grasp_z, yaw=cyaw, speed=0.05)

        # 5. Attempt to grasp
        if not robot.grasp():
            # If grasp failed, open the fingers, retreat and try once more
            robot.release()
            robot.move_to(cx, cy, travel_z, yaw=cyaw, speed=0.2)
            robot.move_to(cx, cy, grasp_z, yaw=cyaw, speed=0.05)
            if not robot.grasp():
                return False   # second attempt also failed

        # 6. Lift the cube to the target height
        robot.move_to(cx, cy, lift_z, yaw=cyaw, speed=0.2)

        # 7. Verify that we are still holding something and that it is high enough
        if robot.holding() is None:
            return False

        final_obs = robot.observe()
        gripper_z = final_obs["gripper"]["pos"][2]
        if gripper_z < 0.05:   # less than 5 cm above the table
            return False

        return True

    except Exception:   # includes MotionError from the safety layer
        # Any unexpected error means we consider the episode a failure
        return False
