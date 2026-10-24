import math


def _avg_pose(robot, name, n=3):
    """Average several noisy pose readings to reduce perception error."""
    xs, ys, zs, yaws = [], [], [], []
    for _ in range(n):
        p = robot.get_pose(name)
        xs.append(p["pos"][0])
        ys.append(p["pos"][1])
        zs.append(p["pos"][2])
        yaws.append(p["yaw"])
    return {
        "pos": [sum(xs) / n, sum(ys) / n, sum(zs) / n],
        "yaw": sum(yaws) / n,
    }


def _pick(robot, cube_name):
    """Approach, grasp and lift the named cube. Returns True if held."""
    for attempt in range(4):
        try:
            cube = _avg_pose(robot, cube_name, 3)
        except Exception:
            return False

        cx, cy, cz = cube["pos"]
        cyaw = cube["yaw"]

        # Small lateral search offsets on later attempts to cope with noise.
        if attempt == 0:
            dx, dy = 0.0, 0.0
        elif attempt == 1:
            dx, dy = 0.006, 0.0
        elif attempt == 2:
            dx, dy = -0.006, 0.0
        else:
            dx, dy = 0.0, 0.006

        tx, ty = cx + dx, cy + dy

        try:
            robot.move_to(tx, ty, 0.12, yaw=cyaw, speed=0.15)
            robot.move_to(tx, ty, 0.015, yaw=cyaw, speed=0.05)
        except Exception:
            try:
                robot.home()
            except Exception:
                pass
            continue

        grasped = robot.grasp()
        if grasped and robot.holding() == cube_name:
            try:
                robot.move_to(tx, ty, 0.14, yaw=cyaw, speed=0.10)
            except Exception:
                try:
                    robot.home()
                except Exception:
                    pass
                continue
            if robot.holding() == cube_name:
                return True

        # Failed grasp: lift clear, open fingers, retry.
        try:
            robot.move_to(tx, ty, 0.12, yaw=cyaw, speed=0.15)
        except Exception:
            try:
                robot.home()
            except Exception:
                pass
        try:
            robot.release()
        except Exception:
            pass

    return False


def _place(robot, tray_name):
    """Lower the held cube into the named tray and release. Returns True on release."""
    for attempt in range(3):
        try:
            tray = _avg_pose(robot, tray_name, 3)
        except Exception:
            return False

        tx, ty, tz = tray["pos"]

        try:
            robot.move_to(tx, ty, 0.14, speed=0.15)
            robot.move_to(tx, ty, 0.03, speed=0.08)
            robot.move_to(tx, ty, 0.016, speed=0.04)
        except Exception:
            try:
                robot.release()
            except Exception:
                pass
            try:
                robot.home()
            except Exception:
                pass
            continue

        try:
            robot.release()
        except Exception:
            pass

        try:
            robot.move_to(tx, ty, 0.12, speed=0.15)
        except Exception:
            try:
                robot.home()
            except Exception:
                pass

        if robot.holding() is None:
            return True

    return False


def _in_tray(robot, cube_name, tray_name):
    """Loose check that the cube centre is inside the tray footprint."""
    try:
        cube = robot.get_pose(cube_name)
        tray = robot.get_pose(tray_name)
    except Exception:
        return False
    dx = cube["pos"][0] - tray["pos"][0]
    dy = cube["pos"][1] - tray["pos"][1]
    return abs(dx) < 0.05 and abs(dy) < 0.05


def run(robot):
    try:
        obs = robot.observe()
    except Exception:
        return False

    objects = obs.get("objects", {})
    fixtures = obs.get("fixtures", {})

    cube_by_color = {}
    for name, info in objects.items():
        if info.get("shape") == "cube":
            cube_by_color[info.get("color")] = name

    tray_by_color = {}
    for name, info in fixtures.items():
        if info.get("kind") == "tray":
            tray_by_color[info.get("color")] = name

    success = True

    for color in ["red", "blue"]:
        cube = cube_by_color.get(color)
        tray = tray_by_color.get(color)
        if cube is None or tray is None:
            success = False
            continue

        placed = False
        for outer in range(3):
            if not _pick(robot, cube):
                break
            if _place(robot, tray):
                if _in_tray(robot, cube, tray):
                    placed = True
                    break
                # Cube released but not verified inside; try again.
            # else: place failed, cube already released; retry from pick.

        if not placed:
            success = False

    try:
        robot.home()
    except Exception:
        pass

    return success
