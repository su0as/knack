import math


def _find_object_by_color(objects, color):
    for name, o in objects.items():
        if o.get("color") == color:
            return name, o
    return None, None


def _find_tray_by_color(fixtures, color):
    for name, f in fixtures.items():
        if f.get("kind") == "tray" and f.get("color") == color:
            return name, f
    return None, None


def _safe_move(robot, x, y, z, yaw=None, speed=None):
    try:
        res = robot.move_to(x, y, z, yaw=yaw, speed=speed)
        return bool(res.get("ok", True))
    except Exception:
        return False


def _pick(robot, name, obj):
    """Approach, descend, grasp. Returns True if the object is held."""
    x, y, z = obj["pos"]
    yaw = obj.get("yaw", 0.0)

    # Move above the cube.
    if not _safe_move(robot, x, y, 0.10, yaw=yaw, speed=0.15):
        return False
    # Descend onto the cube centre.
    if not _safe_move(robot, x, y, z, yaw=yaw, speed=0.06):
        return False
    if robot.grasp():
        return True
    # One nudge retry: lift a touch and re-grasp.
    _safe_move(robot, x, y, z + 0.01, yaw=yaw, speed=0.06)
    _safe_move(robot, x, y, z, yaw=yaw, speed=0.06)
    return bool(robot.grasp())


def _place(robot, tray):
    """Carry to tray, descend, release, retreat."""
    tx, ty, _ = tray["pos"]
    if not _safe_move(robot, tx, ty, 0.12, speed=0.15):
        return False
    if not _safe_move(robot, tx, ty, 0.015, speed=0.06):
        return False
    robot.release()
    _safe_move(robot, tx, ty, 0.12, speed=0.15)
    return True


def run(robot):
    robot.home()
    obs = robot.observe()
    objects = obs["objects"]
    fixtures = obs["fixtures"]

    all_ok = True

    for color in ("red", "blue"):
        cname, cobj = _find_object_by_color(objects, color)
        tname, tray = _find_tray_by_color(fixtures, color)
        if cname is None or tray is None:
            robot.log("missing", color, "cube or tray")
            all_ok = False
            continue

        picked = False
        for attempt in range(2):
            if _pick(robot, cname, cobj):
                picked = True
                break
            # Re-observe in case the cube shifted.
            obs = robot.observe()
            objects = obs["objects"]
            cobj = objects.get(cname, cobj)

        if not picked or robot.holding() != cname:
            robot.log("failed to pick", cname)
            all_ok = False
            continue

        # Lift to a safe carry height before travelling.
        cx, cy, _ = cobj["pos"]
        _safe_move(robot, cx, cy, 0.12, speed=0.15)

        if not _place(robot, tray):
            robot.log("failed to place", cname)
            all_ok = False

    robot.home()
    return all_ok
