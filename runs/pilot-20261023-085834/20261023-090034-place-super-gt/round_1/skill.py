import math

def run(robot):
    """Pick up the blue cube and place it inside the green zone."""
    # Safety: start from a known safe pose
    robot.home()

    # Helper to get the latest pose of an object
    def get_obj_pose(name):
        try:
            return robot.get_pose(name)
        except Exception:
            # Fallback to observe if get_pose fails for any reason
            obs = robot.observe()
            return obs["objects"].get(name)

    # ------------------------------------------------------------------
    # 1. Locate the blue cube
    # ------------------------------------------------------------------
    cube_info = get_obj_pose("blue_cube")
    if cube_info is None:
        robot.log("Blue cube not found in perception")
        return False
    cube_pos = cube_info["pos"]
    cube_yaw = cube_info["yaw"]

    # ------------------------------------------------------------------
    # 2. Grasp the cube (with a couple of retries)
    # ------------------------------------------------------------------
    max_grasp_attempts = 3
    grasped = False
    for attempt in range(max_grasp_attempts):
        try:
            # Move to a safe height above the cube
            above_z = cube_pos[2] + 0.05  # 5 cm above the cube centre
            robot.move_to(cube_pos[0], cube_pos[1], above_z, yaw=cube_yaw, speed=0.15)

            # Lower to a height where the fingertips can reach the cube centre
            # Fingertips are 1.25 cm below the tool point, so we aim for tool point
            # at cube centre + 0.0125 m.
            grasp_z = cube_pos[2] + 0.0125
            robot.move_to(cube_pos[0], cube_pos[1], grasp_z, yaw=cube_yaw, speed=0.08)

            # Close the fingers
            if robot.grasp():
                # Verify that we are actually holding something
                if robot.holding() == "blue_cube":
                    grasped = True
                    robot.log(f"Grasped blue cube on attempt {attempt+1}")
                    break
                else:
                    robot.log("Grasp returned True but not holding blue_cube")
            else:
                robot.log("Grasp returned False")
        except Exception as e:  # catch MotionError or other unexpected issues
            robot.log(f"Move/grasp error on attempt {attempt+1}: {e}")

        # If we failed, open the gripper, retreat a bit and try again
        robot.release()
        robot.move_by(dz=0.05, speed=0.1)  # lift a little to clear the cube

    if not grasped:
        robot.log("Failed to grasp the blue cube after several attempts")
        return False

    # ------------------------------------------------------------------
    # 3. Lift the cube to a safe travel height
    # ------------------------------------------------------------------
    try:
        robot.move_by(dz=0.10, speed=0.15)  # lift 10 cm above grasp point
    except Exception as e:
        robot.log(f"Lift after grasp failed: {e}")
        return False

    # ------------------------------------------------------------------
    # 4. Move over the target zone (green circle)
    # ------------------------------------------------------------------
    target_info = robot.get_pose("target")
    if target_info is None:
        robot.log("Target zone not found")
        return False
    target_pos = target_info["pos"]  # [x, y, 0]

    try:
        # Get current gripper height from observation
        obs = robot.observe()
        current_z = obs["gripper"]["pos"][2]
        # Move horizontally above the target, keep current yaw (doesn't matter much)
        robot.move_to(target_pos[0], target_pos[1], current_z, speed=0.15)
    except Exception as e:
        robot.log(f"Horizontal move to target failed: {e}")
        return False

    # ------------------------------------------------------------------
    # 5. Lower the cube just above the table inside the zone
    # ------------------------------------------------------------------
    try:
        # Aim for a height where the fingertips will be just above the table
        # (table is at z=0, cube centre will be at ~0.015 when placed)
        place_z = 0.02  # 2 cm above table -> fingertips ~0.0075, safe
        robot.move_to(target_pos[0], target_pos[1], place_z, speed=0.08)
    except Exception as e:
        robot.log(f"Lowering to place height failed: {e}")
        return False

    # ------------------------------------------------------------------
    # 6. Release the cube
    # ------------------------------------------------------------------
    robot.release()
    robot.log("Released blue cube")

    # Optional: quick check that we are no longer holding anything
    if robot.holding() is not None:
        robot.log("Still holding something after release")
        return False

    # ------------------------------------------------------------------
    # 7. Retreat to a safe height
    # ------------------------------------------------------------------
    try:
        robot.move_by(dz=0.10, speed=0.15)
    except Exception as e:
        robot.log(f"Retreat after place failed: {e}")
        return False

    robot.log("Place operation completed")
    return True
