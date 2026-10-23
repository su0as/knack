# skill module
import math
import itertools

def run(robot):
    """
    Stack the red cube on top of the blue cube and let go.
    Return True if stacking succeeded, otherwise False.
    """

    # ------------------------------------------------------------------
    # 1. Locate the red and blue cubes and ensure they are on the table
    # ------------------------------------------------------------------
    def find_color(target_color, max_tries=2):
        for _ in range(max_tries):
            obs = robot.observe()
            for name, obj in obs["objects"].items():
                if obj["color"] == target_color:
                    return name, obs
            robot.wait(0.05)
        return None, None

    red_name, obs = find_color("red")
    blue_name, obs = find_color("blue")
    if red_name is None or blue_name is None:
        robot.log("Red or blue cube not found")
        return False

    # Verify both cubes sit on the table (z ≈ 0.015 m)
    for name in (red_name, blue_name):
        p = robot.get_pose(name)
        if not (abs(p["pos"][2] - 0.015) < 0.02):
            robot.log(f"{name} not on table surface")
            return False

    # ------------------------------------------------------------------
    # 2. Get initial precise poses
    # ------------------------------------------------------------------
    red_pose = robot.get_pose(red_name)
    blue_pose = robot.get_pose(blue_name)

    red_x, red_y, red_z = red_pose["pos"]
    red_yaw = red_pose["yaw"]
    blue_x, blue_y, blue_z = blue_pose["pos"]

    # ------------------------------------------------------------------
    # 3. Approach and grasp the red cube
    # ------------------------------------------------------------------
    try:
        robot.move_to(red_x, red_y, red_z, yaw=red_yaw, speed=0.07)
    except Exception as e:          # MotionError or safety halt
        robot.log(f"Move to red failed: {e}")
        return False

    if not robot.grasp():
        robot.log("Grasp command failed")
        return False

    # Verify that the red cube is actually held; retry a few times
    for _ in range(3):
        if robot.holding() == red_name:
            break
        robot.log("Hold verification retry")
        robot.wait(0.4)
    else:
        robot.log("Failed to hold red cube after retries")
        robot.release()
        return False

    # ------------------------------------------------------------------
    # 4. Re‑observe to get a fresh blue‑cube pose (may have shifted)
    # ------------------------------------------------------------------
    blue_obs = robot.observe()
    # Find the blue cube name again in the new observation
    blue_name2 = None
    for n, o in blue_obs["objects"].items():
        if o["color"] == "blue":
            blue_name2 = n
            break
    if blue_name2 is None:
        robot.log("Blue cube disappeared during lift")
        robot.release()
        return False

    blue_pose2 = robot.get_pose(blue_name2)
    b_x, b_y, b_z = blue_pose2["pos"]
    # Expected centre height of the red cube when stacked on the blue cube
    place_center_z = b_z + 0.03   # blue height + half‑heights (≈0.03 m)

    # ------------------------------------------------------------------
    # 5. Lift to a safe height above the blue cube (using fresh XY)
    # ------------------------------------------------------------------
    safe_z = b_z + 0.05           # a small clearance
    try:
        robot.move_to(b_x, b_y, safe_z, yaw=red_yaw, speed=0.07)
    except Exception as e:
        robot.log(f"Move to safe height failed: {e}")
        robot.release()
        return False

    # ------------------------------------------------------------------
    # 6. Lower to the placement height
    # ------------------------------------------------------------------
    try:
        robot.move_to(b_x, b_y, place_center_z, yaw=red_yaw, speed=0.05)
    except Exception as e:
        robot.log(f"Move to placement height failed: {e}")
        robot.release()
        return False

    # ------------------------------------------------------------------
    # 7. Release only if we are still holding the red cube
    # ------------------------------------------------------------------
    if robot.holding() != red_name:
        robot.log("Lost grip just before release")
        robot.release()
        return False
    robot.release()
    robot.wait(0.2)               # let the release settle

    # ------------------------------------------------------------------
    # 8. Final validation: check that the released cube is at the correct height
    # ------------------------------------------------------------------
    final_pose = robot.get_pose(red_name)
    if abs(final_pose["pos"][2] - place_center_z) > 0.015:
        robot.log(
            f"Release height error: got {final_pose['pos'][2]:.4f}, "
            f"expected {place_center_z:.4f}"
        )
        return False

    # ------------------------------------------------------------------
    # 9. Return to a neutral pose and report success
    # ------------------------------------------------------------------
    robot.home()
    return True
