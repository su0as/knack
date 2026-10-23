import math

def run(robot):
    """
    Pick up the red cube and hold it at least 5 cm above the table.
    Returns True if the maneuver appears successful, False otherwise.
    """
    MAX_GRASP_ATTEMPTS = 2

    try:
        # 1. Observe scene to get red cube pose and size
        obs = robot.observe()
        cube = obs["objects"]["red_cube"]
        cx, cy, cz = cube["pos"]          # centre of the cube
        cyaw = cube["yaw"]                # orientation for finger alignment
        cube_height = cube["size"][2]     # vertical size (z dimension)
        half_h = cube_height / 2.0

        # 2. Compute grasp height so that finger pads sit at cube's mid-height.
        #    Finger pads are 1.25 cm below the tool point.
        grasp_z = cz + half_h + 0.0125    # tool point height
        # 3. Lift high enough to guarantee >5 cm clearance above table.
        lift_z = cz + 0.20                # increased offset per failure analysis
        # 4. Travel height to avoid collisions while moving between poses.
        travel_z = cz + 0.25

        # Helper to attempt a grasp at the current pose.
        def attempt_grasp():
            # Close fingers; returns True if something is held.
            return robot.grasp()

        # 5. Move to travel height above the cube.
        robot.move_to(cx, cy, travel_z, yaw=cyaw, speed=0.2)

        # 6. Descend to grasp position (slow for precision).
        robot.move_to(cx, cy, grasp_z, yaw=cyaw, speed=0.05)

        # 7. Try to grasp, with a limited number of retries.
        grasp_success = False
        for _ in range(MAX_GRASP_ATTEMPTS):
            if attempt_grasp():
                grasp_success = True
                break
            # Grasp failed: open fingers, retreat, try again.
            robot.release()
            robot.move_to(cx, cy, travel_z, yaw=cyaw, speed=0.2)
            robot.move_to(cx, cy, grasp_z, yaw=cyaw, speed=0.05)

        if not grasp_success:
            return False

        # 8. Verify we actually hold the red cube.
        if robot.holding() != "red_cube":
            return False

        # 9. Let the gripper settle after a successful grasp.
        robot.wait(0.1)

        # 10. Lift the cube to the target height (slower to avoid slip).
        robot.move_to(cx, cy, lift_z, yaw=cyaw, speed=0.1)

        # 11. Post‑lift sanity check: gripper high enough and still holding.
        obs_after = robot.observe()
        gripper_z = obs_after["gripper"]["pos"][2]
        if gripper_z < 0.05:          # less than 5 cm above table
            return False
        if robot.holding() != "red_cube":
            return False

        # 12. Final verification.
        final_obs = robot.observe()
        final_gripper_z = final_obs["gripper"]["pos"][2]
        if final_gripper_z < 0.05:
            return False
        if robot.holding() is None:
            return False

        return True

    except Exception:   # includes MotionError from the safety layer
        # Any unexpected error means we consider the episode a failure.
        return False
