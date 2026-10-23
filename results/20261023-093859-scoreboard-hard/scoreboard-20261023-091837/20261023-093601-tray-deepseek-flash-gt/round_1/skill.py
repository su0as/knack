import math


def run(robot):
    obs = robot.observe()
    objects = obs["objects"]
    fixtures = obs["fixtures"]

    # --- Locate the yellow cube ---
    cube_name = None
    cube_info = None
    for name, o in objects.items():
        if o.get("color") == "yellow":
            cube_name, cube_info = name, o
            break
    if cube_info is None:
        robot.log("no yellow cube found")
        return False

    # --- Locate the tray ---
    tray_info = None
    for name, f in fixtures.items():
        if f.get("kind") == "tray":
            tray_info = f
            break
    if tray_info is None:
        robot.log("no tray found")
        return False

    tx, ty = tray_info["pos"][0], tray_info["pos"][1]
    inner = tray_info.get("inner_half_size", 0.04)

    # --- Grasp the cube (bounded retries) ---
    grasped = False
    cx, cy, cz = cube_info["pos"]
    yaw = cube_info["yaw"]

    for attempt in range(3):
        try:
            pose = robot.get_pose(cube_name)
            cx, cy, cz = pose["pos"]
            yaw = pose["yaw"]
        except Exception:
            pass

        try:
            robot.move_to(cx, cy, 0.10, yaw=yaw, speed=0.15)
            robot.move_to(cx, cy, 0.015, yaw=yaw, speed=0.05)
        except Exception:
            robot.log("approach failed", attempt)
            robot.release()
            robot.home()
            continue

        if robot.grasp():
            grasped = True
            break

        robot.log("grasp attempt failed", attempt)
        robot.release()
        try:
            robot.move_to(cx, cy, 0.10, yaw=yaw, speed=0.1)
        except Exception:
            pass

    if not grasped:
        robot.log("could not grasp cube")
        robot.home()
        return False

    # --- Carry the cube to the tray ---
    try:
        robot.move_to(cx, cy, 0.12, yaw=yaw, speed=0.1)
        robot.move_to(tx, ty, 0.12, speed=0.15)
        robot.move_to(tx, ty, 0.02, speed=0.05)
    except Exception:
        robot.log("carry failed")
        robot.release()
        robot.home()
        return False

    # --- Release and retreat ---
    robot.release()
    try:
        robot.move_to(tx, ty, 0.12, speed=0.1)
    except Exception:
        pass
    robot.home()

    # --- Verify placement ---
    obs2 = robot.observe()
    if cube_name in obs2["objects"]:
        p = obs2["objects"][cube_name]["pos"]
        if abs(p[0] - tx) <= inner + 0.015 and abs(p[1] - ty) <= inner + 0.015:
            return True
    return False
