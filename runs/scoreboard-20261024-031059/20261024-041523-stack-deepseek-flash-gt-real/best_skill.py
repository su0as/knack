import math


def _median(vals):
    s = sorted(vals)
    n = len(s)
    if n == 0:
        return 0.0
    if n % 2 == 1:
        return s[n // 2]
    return 0.5 * (s[n // 2 - 1] + s[n // 2])


def _robust_pos(robot, name, n=7):
    """Median of n noisy pose readings -> robust (x, y, z)."""
    xs, ys, zs = [], [], []
    for _ in range(n):
        try:
            p = robot.get_pose(name)["pos"]
        except Exception:
            continue
        xs.append(p[0])
        ys.append(p[1])
        zs.append(p[2])
    if not xs:
        return None
    return (_median(xs), _median(ys), _median(zs))


def _robust_yaw(robot, name, n=5):
    vals = []
    for _ in range(n):
        try:
            vals.append(robot.get_pose(name)["yaw"])
        except Exception:
            continue
    if not vals:
        return 0.0
    return _median(vals)


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

    # ---------- Grasp the red cube ----------
    # Spiral of small XY offsets so one bad reading does not doom the episode.
    offsets = [
        (0.0, 0.0),
        (0.006, 0.0), (-0.006, 0.0),
        (0.0, 0.006), (0.0, -0.006),
        (0.006, 0.006), (-0.006, -0.006),
        (0.006, -0.006), (-0.006, 0.006),
    ]

    grasped = False
    for dx, dy in offsets:
        rp = _robust_pos(robot, red, 7)
        if rp is None:
            break
        ryaw = _robust_yaw(robot, red, 5)
        tx, ty = rp[0] + dx, rp[1] + dy
        try:
            robot.move_to(tx, ty, 0.08, yaw=ryaw, speed=0.15)
            robot.move_to(tx, ty, 0.015, yaw=ryaw, speed=0.05)
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

    # ---------- Move above the blue cube ----------
    bp = _robust_pos(robot, blue, 9)
    if bp is None:
        robot.log("cannot see blue cube")
        return False

    try:
        robot.move_to(bp[0], bp[1], 0.12, speed=0.15)
    except Exception:
        robot.log("cannot reach above blue cube")
        return False

    # ---------- Closed-loop XY alignment of held red over blue ----------
    for _ in range(4):
        if robot.holding() != red:
            robot.log("lost red cube during alignment")
            return False
        rp = _robust_pos(robot, red, 7)
        bp = _robust_pos(robot, blue, 7)
        if rp is None or bp is None:
            break
        ex = bp[0] - rp[0]
        ey = bp[1] - rp[1]
        if abs(ex) < 0.002 and abs(ey) < 0.002:
            break
        try:
            robot.move_by(dx=ex, dy=ey, speed=0.05)
        except Exception:
            break

    # ---------- Descend and release ----------
    bp = _robust_pos(robot, blue, 7)
    if bp is None:
        return False
    place_z = bp[2] + 0.031          # red centre = blue centre + 0.030
    if place_z < 0.044:
        place_z = 0.044
    if place_z > 0.050:
        place_z = 0.050

    try:
        robot.move_to(bp[0], bp[1], place_z, speed=0.04)
    except Exception:
        robot.log("failed to reach place position")
        return False

    robot.release()
    # Lift straight up before retreating so the cube is not dragged sideways.
    try:
        robot.move_by(dz=0.03, speed=0.05)
    except Exception:
        pass
    try:
        robot.move_to(0.16, 0.0, 0.14, speed=0.15)
    except Exception:
        pass
    robot.home()
    robot.wait(0.3)

    # ---------- Verify the stack ----------
    try:
        rp = _robust_pos(robot, red, 5)
        bp = _robust_pos(robot, blue, 5)
        if rp is not None and bp is not None:
            dz = rp[2] - bp[2]
            dxy = math.hypot(rp[0] - bp[0], rp[1] - bp[1])
            robot.log("stack check dz=%.4f dxy=%.4f" % (dz, dxy))
            if dz > 0.02 and dxy < 0.025:
                return True
    except Exception:
        pass

    return False
