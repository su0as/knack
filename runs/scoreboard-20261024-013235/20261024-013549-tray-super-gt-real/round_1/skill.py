import math

def run(robot):
    # Helper to attempt a grasp with retries
    def attempt_grasp(cube_pose, max_tries=3):
        for i in range(max_tries):
            # Approach from above, aligning with cube yaw
            x, y, z = cube_pose["pos"]
            yaw = cube_pose["yaw"]
            # Move to a point just above the cube
            above_z = z + 0.08  # 8 cm clearance
            try:
                res = robot.move_to(x, y, above_z, yaw=yaw, speed=0.1)
                if not res["ok"]:
                    continue
                # Lower slowly to grasp height (around cube centre)
                res = robot.move_to(x, y, z, yaw=yaw, speed=0.05)
                if not res["ok"]:
                    continue
                # Close fingers
                if robot.grasp():
                    # Verify hold
                    if robot.holding() is not None:
                        # Lift up
                        robot.move_to(x, y, above_z, yaw=yaw, speed=0.05)
                        return True
            except Exception as e:  # MotionError or others
                robot.log("grasp attempt failed:", e)
                continue
        return False

    # 1. Home
    robot.home()

    # 2. Locate yellow cube
    obs = robot.observe()
    cube_info = obs["objects"].get("yellow_cube")
    if cube_info is None:
        robot.log("Yellow cube not perceived")
        return False

    # 3. Grasp the cube
    if not attempt_grasp(cube_info):
        robot.log("Failed to grasp yellow cube after retries")
        return False

    # 4. Get tray pose (use latest perception)
    obs = robot.observe()
    tray_info = obs["fixtures"].get("tray")
    if tray_info is None:
        robot.log("Tray not perceived")
        return False
    tx, ty, tz = tray_info["pos"]  # tz is 0 (table top)

    # 5. Move above tray
    try:
        res = robot.move_to(tx, ty, tz + 0.12, speed=0.1)  # 12 cm above tray
        if not res["ok"]:
            robot.log("Failed to move above tray")
            return False
    except Exception as e:
        robot.log("Motion error moving above tray:", e)
        return False

    # 6. Lower to table height inside tray (cube centre height)
    try:
        res = robot.move_to(tx, ty, tz + 0.015, speed=0.05)  # cube centre height
        if not res["ok"]:
            robot.log("Failed to lower over tray")
            return False
    except Exception as e:
        robot.log("Motion error lowering over tray:", e)
        return False

    # 7. Release
    robot.release()
    if robot.holding() is not None:
        robot.log("Failed to release cube")
        return False

    # 8. Retract a bit
    try:
        robot.move_by(dz=0.08, speed=0.05)
    except Exception:
        pass

    # 9. Home again (optional)
    robot.home()
    return True
