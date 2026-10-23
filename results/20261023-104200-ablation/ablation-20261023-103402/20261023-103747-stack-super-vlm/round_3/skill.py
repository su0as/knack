import math

def run(robot):
    """Stack the red cube on top of the blue cube."""
    try:
        # Start from a known safe pose
        robot.home()

        # Get current poses
        red_pose = robot.get_pose("red_cube")
        blue_pose = robot.get_pose("blue_cube")

        cube_height = 0.03          # all cubes are 0.03 m side
        half_height = cube_height / 2.0

        # Helper to perform a move and verify success
        def safe_move_to(**kwargs):
            res = robot.move_to(**kwargs)
            if not res.get("ok", False):
                robot.log(f"Move failed: {res}")
                return False
            return True

        # ---- Grasp red cube ----
        # Approach from above
        above_red = {
            "x": red_pose["pos"][0],
            "y": red_pose["pos"][1],
            "z": 0.05,          # clearance
            "yaw": red_pose["yaw"]
        }
        if not safe_move_to(**above_red):
            return False

        # Descend to grasp height (center of cube)
        grasp_target = {
            "x": red_pose["pos"][0],
            "y": red_pose["pos"][1],
            "z": red_pose["pos"][2] + half_height,  # center z
            "yaw": red_pose["yaw"]
        }
        if not safe_move_to(**grasp_target, speed=0.08):
            return False

        # Close fingers
        if not robot.grasp():
            robot.log("Grasp failed on red cube")
            return False

        # Verify hold
        if robot.holding() != "red_cube":
            robot.log("Did not hold red cube after grasp")
            return False

        # Lift to clearance
        lift_red = {
            "x": red_pose["pos"][0],
            "y": red_pose["pos"][1],
            "z": 0.05,
            "yaw": red_pose["yaw"]
        }
        if not safe_move_to(**lift_red):
            return False

        # ---- Move over blue cube and stack ----
        # Approach from above
        above_blue = {
            "x": blue_pose["pos"][0],
            "y": blue_pose["pos"][1],
            "z": 0.05,
            "yaw": blue_pose["yaw"]
        }
        if not safe_move_to(**above_blue):
            return False

        # Compute target height for red cube center when stacked:
        # red_center_z = blue_center_z + cube_height
        target_z = blue_pose["pos"][2] + cube_height
        stack_target = {
            "x": blue_pose["pos"][0],
            "y": blue_pose["pos"][1],
            "z": target_z,
            "yaw": blue_pose["yaw"]
        }
        if not safe_move_to(**stack_target, speed=0.05):  # reduced speed for precision
            return False

        # Small upward lift before releasing to ensure clearance during release
        lift_before_release = {
            "x": blue_pose["pos"][0],
            "y": blue_pose["pos"][1],
            "z": target_z + 0.015,  # increased clearance to 15 mm
            "yaw": blue_pose["yaw"]
        }
        if not safe_move_to(**lift_before_release, speed=0.05):  # reduced speed
            return False

        # Release red cube onto blue cube
        robot.release()
        robot.wait(0.2)  # let it settle

        # Verify release
        if robot.holding() is not None:
            robot.log("Still holding after release")
            return False

        # Retreat to clearance (above blue cube)
        retreat = {
            "x": blue_pose["pos"][0],
            "y": blue_pose["pos"][1],
            "z": 0.05,
            "yaw": blue_pose["yaw"]
        }
        if not safe_move_to(**retreat):
            return False

        # Final safety pose
        robot.home()
        return True

    except Exception as e:
        robot.log(f"Exception during stacking: {e}")
        return False
