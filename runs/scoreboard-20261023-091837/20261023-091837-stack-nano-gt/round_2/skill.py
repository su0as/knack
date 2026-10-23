# skill module
import math
import itertools

def run(robot):
    """
    Stack the red cube on top of the blue cube and let go.
    Return True if stacking succeeded, otherwise False.
    """

    # ------------------------------------------------------------------
    # 1. Perceive the scene (with a quick re‑observe if needed)
    # ------------------------------------------------------------------
    def find_object(target_color, max_tries=2):
        for _ in range(max_tries):
            obs = robot.observe()
            for name, obj in obs["objects"].items():
                if obj["color"] == target_color:
                    return name, obs
            # not found – try one more observation (helps with brief occlusions)
            robot.wait(0.1)
        return None, None

    red_name, obs = find_object("red")
    blue_name, obs = find_object("blue")
    if red_name is None or blue_name is None:
        robot.log("Red or blue cube not found after re‑observation")
        return False

    # Verify both cubes are on the table (z ≈ 0.015 m)
    red_pose0 = robot.get_pose(red_name)
    blue_pose0 = robot.get_pose(blue_name)
    if not (abs(red_pose0["pos"][2] - 0.015) < 0.02 and
            abs(blue_pose0["pos"][2] - 0.015) < 0.02):
        robot.log("Red or blue cube not on table surface")
        return False

    # ------------------------------------------------------------------
    # 2. Get precise poses (includes ~2 mm noise)
    # ------------------------------------------------------------------
    red_pose = robot.get_pose(red_name)
    blue_pose = robot.get_pose(blue_name)

    red_x, red_y, red_z = red_pose["pos"]
    red_yaw = red_pose["yaw"]
    blue_x, blue_y, blue_z = blue_pose["pos"]

    # ------------------------------------------------------------------
    # 3. Move to red cube and grasp it
    # ------------------------------------------------------------------
    try:
        robot.move_to(red_x, red_y, red_z, yaw=red_yaw, speed=0.07)
    except Exception as e:          # MotionError or safety halt
        robot.log(f"Move to red failed: {e}")
        return False

    # Close fingers; verify that we are actually holding the red cube
    if not robot.grasp():
        robot.log("Grasp command failed")
        return False

    # Verify hold; retry a few times if needed
    max_retries = 3
    for i in range(max_retries):
        if robot.holding() == red_name:
            break
        robot.log(f"Hold verification failed, retry {i+1}/{max_retries}")
        robot.wait(0.5)
    else:
        robot.log("Failed to hold red cube after retries")
        robot.release()
        return False

    # ------------------------------------------------------------------
    # 4. Lift and translate above the blue cube
    # ------------------------------------------------------------------
    # Height of the red cube's centre when stacked on top of the blue cube:
    #   blue centre (blue_z) + full height of blue (≈0.03 m) + half height of red (≈0.015 m)
    #   => blue_z + 0.03 m
    place_center_z = blue_z + 0.03

    # First move to a safe height above the blue cube
    safe_z = blue_z + 0.05
    try:
        robot.move_to(blue_x, blue_y, safe_z, yaw=red_yaw, speed=0.07)
    except Exception as e:
        robot.log(f"Move to safe height failed: {e}")
        robot.release()
        return False

    # Lower slowly to the placement height
    try:
        robot.move_to(blue_x, blue_y, place_center_z, yaw=red_yaw, speed=0.05)
    except Exception as e:
        robot.log(f"Move to placement height failed: {e}")
        robot.release()
        return False

    # Ensure we are still holding before releasing
    if robot.holding() != red_name:
        robot.log("Lost grip on red cube before release")
        robot.release()
        return False

    # ------------------------------------------------------------------
    # 5. Release the red cube
    # ------------------------------------------------------------------
    robot.release()
    robot.wait(0.2)  # give time for the release to settle

    # ------------------------------------------------------------------
    # 6. Verify that the red cube is now stacked correctly
    # ------------------------------------------------------------------
    # Re‑observe to get the new pose of the red cube (it may have settled)
    try:
        red_pose_after = robot.get_pose(red_name)
    except Exception:
        # If we cannot get the pose, assume failure
        robot.log("Could not verify red cube pose after release")
        robot.home()
        return False

    expected_z = blue_z + 0.03
    red_z_after = red_pose_after["pos"][2]
    if abs(red_z_after - expected_z) > 0.01:
        robot.log(f"Red cube not at expected stacked height (got {red_z_after:.4f}, expected {expected_z:.4f})")
        robot.home()
        return False

    # ------------------------------------------------------------------
    # 7. Optional: return to a neutral pose and report success
    # ------------------------------------------------------------------
    robot.home()
    return True
