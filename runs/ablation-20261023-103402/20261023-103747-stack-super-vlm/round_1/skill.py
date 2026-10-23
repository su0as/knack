import math

def run(robot):
    """Stack the red cube on top of the blue cube."""
    try:
        # Start from a known safe pose
        robot.home()

        # Get current poses
        obs = robot.observe()
        red_pose = robot.get_pose("red_cube")
        blue_pose = robot.get_pose("blue_cube")

        # Cube half-size (all cubes are 0.03 m side)
        half = 0.03 / 2.0  # 0.015 m

        # ---- Grasp red cube ----
        # Approach from above
        above_red = {
            "x": red_pose["pos"][0],
            "y": red_pose["pos"][1],
            "z": 0.05,          # clearance
            "yaw": red_pose["yaw"]
        }
        robot.move_to(**above_red, speed=0.15)

        # Descend to grasp height (center of cube)
        grasp_target = {
            "x": red_pose["pos"][0],
            "y": red_pose["pos"][1],
            "z": red_pose["pos"][2],  # center z
            "yaw": red_pose["yaw"]
        }
        robot.move_to(**grasp_target, speed=0.08)

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
        robot.move_to(**lift_red, speed=0.15)

        # ---- Move over blue cube ----
        above_blue = {
            "x": blue_pose["pos"][0],
            "y": blue_pose["pos"][1],
            "z": 0.05,
            "yaw": blue_pose["yaw"]
        }
        robot.move_to(**above_blue, speed=0.15)

        # Descend to just above blue cube (center)
        above_blue_center = {
            "x": blue_pose["pos"][0],
            "y": blue_pose["pos"][1],
            "z": blue_pose["pos"][2],  # center of blue cube
            "yaw": blue_pose["yaw"]
        }
        robot.move_to(**above_blue_center, speed=0.08)

        # Compute target height for red cube center when stacked:
        # red_center_z = blue_center_z + cube_height (0.03)
        target_z = blue_pose["pos"][2] + 0.03
        stack_target = {
            "x": blue_pose["pos"][0],
            "y": blue_pose["pos"][1],
            "z": target_z,
            "yaw": blue_pose["yaw"]
        }
        robot.move_to(**stack_target, speed=0.08)

        # Release red cube onto blue cube
        robot.release()
        robot.wait(0.2)  # let it settle

        # Retreat to clearance
        retreat = {
            "x": blue_pose["pos"][0],
            "y": blue_pose["pos"][1],
            "z": 0.05,
            "yaw": blue_pose["yaw"]
        }
        robot.move_to(**retreat, speed=0.15)

        # Final safety pose
        robot.home()
        return True

    except Exception as e:
        robot.log(f"Exception during stacking: {e}")
        return False
