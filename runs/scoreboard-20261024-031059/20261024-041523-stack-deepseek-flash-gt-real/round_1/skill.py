import math


def _avg_pos(robot, name, n=3):
    xs = []
    ys = []
    zs = []
    for _ in range(n):
        p = robot.get_pose(name)
        xs.append(p["pos"][0])
        ys.append(p["pos"][1])
        zs.append(p["pos"][2])
    return (sum(xs) / n, sum(ys) / n, sum(zs) / n)


def _find(robot, color):
    obs = robot.observe()
    for name, o in obs["objects"].items():
        if o.get("color") == color:
            return name
    return None


def run(robot):
    robot.home()

    red = _find(robot, "red")
    blue = _find(robot, "blue")
    if red is None or blue is None:
        robot.log("missing cubes", red, blue)
        return False

    red_yaw = robot.get_pose(red)["yaw"]

    # Spiral of small XY offsets to recover from a bad camera reading.
    offsets = [
        (0.0, 0.0),
        (0.006, 0.0), (-0.006, 0.0),
        (0.0, 0.006), (0.0, -0.006),
        (0.006, 0.006), (-0.006, -0.006),
        (0.006, -0.006), (-0.006, 0.006),
    ]

    grasped = False
    for dx, dy in offsets:
        x, y, z = _avg_pos(robot, red)
        tx, ty = x + dx, y + dy
        try:
            robot.move_to(tx, ty, 0.08, yaw=red_yaw, speed=0.15)
            robot.move_to(tx, ty, 0.015, yaw=red_yaw, speed=0.05)
        except Exception:
            try:
                robot.move_to(tx, ty, 0.08, speed=0.15)
            except Exception:
                pass
            continue

        if robot.grasp() and robot.holding() == red:
            grasped = True
            break

        robot.release()
        try:
            robot.move_to(tx, ty, 0.08, speed=0.15)
        except Exception:
            pass

    if not grasped:
        robot.log("failed to grasp red cube")
        return False

    # Lift straight up.
    try:
        robot.move_by(dz=0.08, speed=0.15)
    except Exception:
        pass

    if robot.holding() != red:
        robot.log("lost red cube during lift")
        return False

    # Estimate how far the cube centre sits from the tool point while held.
    off_x = 0.0
    off_y = 0.0
    try:
        n = 3
        gx = gy = rx = ry = 0.0
        for _ in range(n):
            g = robot.observe()["gripper"]["pos"]
            r = robot.get_pose(red)["pos"]
            gx += g[0]
            gy += g[1]
            rx += r[0]
            ry += r[1]
        ox = (rx - gx) / n
        oy = (ry - gy) / n
        # Only trust the estimate if it is small and plausible.
        if abs(ox) < 0.015 and abs(oy) < 0.015:
            off_x, off_y = ox, oy
    except Exception:
        pass

    bx, by, bz = _avg_pos(robot, blue)
    place_x = bx - off_x
    place_y = by - off_y
    place_z = 0.046  # red bottom ~0.031, blue top ~0.030

    try:
        robot.move_to(place_x, place_y, 0.12, speed=0.15)
        robot.move_to(place_x, place_y, place_z, speed=0.05)
    except Exception:
        robot.log("failed to reach place position")
        return False

    robot.release()
    try:
        robot.move_to(place_x, place_y, 0.12, speed=0.15)
    except Exception:
        pass
    robot.home()
    robot.wait(0.3)

    # Verify the stack.
    try:
        rp = robot.get_pose(red)["pos"]
        bp = robot.get_pose(blue)["pos"]
        dz = rp[2] - bp[2]
        dxy = math.hypot(rp[0] - bp[0], rp[1] - bp[1])
        robot.log("stack check dz=%.4f dxy=%.4f" % (dz, dxy))
        if dz > 0.02 and dxy < 0.025:
            return True
    except Exception:
        pass

    return False
