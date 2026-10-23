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
        grasp_z = cz + 0.02               # 2 cm above centre → finger pads around middle
        lift_z = cz + 0.15                # 15 cm above centre → safely >5 cm above table
        travel_z = cz + 0.20              # travel height to avoid collisions

        # 3. Move to a safe pose above the cube
        robot.move_to(cx, cy, travel_z, yaw=cyaw, speed=0.2)

        # 4. Descend to the grasp position (slow for precision)
        robot.move_to(cx, cy, grasp_z, yaw=cyaw, speed=0.05)

        # 5. Attempt to grasp (with one retry)
        if not robot.grasp():
            robot.release()
            robot.move_to(cx, cy, travel_z, yaw=cyaw, speed=0.2)
            robot.move_to(cx, cy, grasp_z, yaw=cyaw, speed=0.05)
            if not robot.grasp():
                return False   # second attempt also failed

        # Confirm we actually have the cube before lifting
        if robot.holding() != "red_cube":
            return False

        # Let the gripper settle after a successful grasp
        robot.wait(0.1)

        # 6. Lift the cube to the target height (slower to avoid slip)
        robot.move_to(cx, cy, lift_z, yaw=cyaw, speed=0.1)

        # 7. Post‑lift sanity check: gripper should be high enough and still holding
        obs_after_lift = robot.observe()
        gripper_z = obs_after_lift["gripper"]["pos"][2]
        if gripper_z < 0.05:          # less than 5 cm above table → insufficient lift
            return False
        if robot.holding() != "red_cube":
            return False

        # 8. Final verification: still holding and high enough
        final_obs = robot.observe()
        gripper_z_final = final_obs["gripper"]["pos"][2]
        if gripper_z_final < 0.05:    # less than 5 cm above table
            return False
        if robot.holding() is None:
            return False

        return True

    except Exception:   # includes MotionError from the safety layer
        # Any unexpected error means we consider the episode a failure
        return False
