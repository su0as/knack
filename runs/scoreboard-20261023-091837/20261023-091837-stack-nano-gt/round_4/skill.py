# skill module
import math
import itertools

def run(robot):
    """
    Stack the red cube on top of the blue cube and let go.
    Return True if successful, otherwise False.
    """

    # ------------------------------------------------------------------
    # 1. Locate the red and blue cubes
    # ------------------------------------------------------------------
    def find_color(target_color, attempts=2):
        for _ in range(attempts):
            obs = robot.observe()
            for name, obj in obs["objects"].items():
                if obj["color"] == target_color:
                    return name
            robot.wait(0.05)
        return None

    red_name = find_color("red")
    blue_name = find_color("blue")
    if red_name is None or blue_name is None:
        robot.log("Red or blue cube not found")
        return False

    # ------------------------------------------------------------------
    # 2. Verify both cubes sit on the table (z ≈ 0.015 m)
    # ------------------------------------------------------------------
    for name in (red_name, blue_name):
        p = robot.get_pose(name)
        if abs(p["pos"][2] - 0.015) > 0.02:
            robot.log(f"{name} not on table surface (z={p['pos'][2]:.3f})")
            return False

    # ------------------------------------------------------------------
    # 3. Get initial precise poses
    # ------------------------------------------------------------------
    red_pose = robot.get_pose(red_name)
    blue_pose = robot.get_pose(blue_name)

    red_x, red_y, red_z = red_pose["pos"]
    red_yaw = red_pose["yaw"]
    blue_x, blue_y, blue_z = blue_pose["pos"]

    # ------------------------------------------------------------------
    # 4. Approach and grasp the red cube
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
    # 5. Re‑observe to get fresh blue‑cube pose (handles possible drift)
    # ------------------------------------------------------------------
    obs = robot.observe()
    # locate blue cube again
    blue_name2 = None
    for name, obj in obs["objects"].items():
        if obj["color"] == "blue":
            blue_name2 = name
            break
    if blue_name2 is None:
        robot.log("Blue cube disappeared before placement")
        robot.release()
        return False
    blue_pose2 = robot.get_pose(blue_name2)
    b_x, b_y, b_z = blue_pose2["pos"]
    b_yaw = blue_pose2["yaw"]

    # ------------------------------------------------------------------
    # 6. Lift to a safe height above the blue cube
    # ------------------------------------------------------------------
    safe_z = b_z + 0.05  # small clearance
    try:
        robot.move_to(b_x, b_y, safe_z, yaw=red_yaw, speed=0.07)
    except Exception as e:
        robot.log(f"Move to safe height failed: {e}")
        robot.release()
        return False

    # ------------------------------------------------------------------
    # 7. Lower to the calculated stacking height
    # ------------------------------------------------------------------
    place_center_z = b_z + 0.03  # cube height ≈ 0.03 m (0.015 each)
    try:
        robot.move_to(b_x, b_y, place_center_z, yaw=red_yaw, speed=0.05)
    except Exception as e:
        robot.log(f"Move to placement height failed: {e}")
        robot.release()
        return False

    # ------------------------------------------------------------------
    # 8. Confirm grip is still intact just before release
    # ------------------------------------------------------------------
    if robot.holding() != red_name:
        robot.log("Lost grip immediately before release")
        robot.release()
        return False

    # ------------------------------------------------------------------
    # 9. Release the red cube
    # ------------------------------------------------------------------
    robot.release()
    robot.wait(0.2)  # allow release to settle

    # ------------------------------------------------------------------
    # 10. Verify final stacked pose
    # ------------------------------------------------------------------
    final_obs = robot.observe()
    # find red cube name in the final observation
    red_name_final = None
    for name, obj in final_obs["objects"].items():
        if obj["color"] == "red":
            red_name_final = name
            break
    if red_name_final is None:
        robot.log("Red cube vanished after release")
        return False
    final_pose = robot.get_pose(red_name_final)
    f_x, f_y, f_z = final_pose["pos"]

    expected_x, expected_y = b_x, b_y
    expected_z = place_center_z

    # XY tolerance
    if abs(f_x - expected_x) > 0.015 or abs(f_y - expected_y) > 0.015:
        robot.log(f"XY mis‑alignment after placement: {f_x:.3f},{f_y:.3f} vs {expected_x:.3f},{expected_y:.3f}")
        return False

    # Z gap tolerance
    if abs(f_z - expected_z) > 0.015:
        robot.log(f"Z gap error after placement: {f_z:.3f} vs {expected_z:.3f}")
        return False

    # ------------------------------------------------------------------
    # 11. Return to a neutral pose and signal success
    # ------------------------------------------------------------------
    robot.home()
    return True
