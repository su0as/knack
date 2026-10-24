import math


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _avg_pose(robot, name, n=6):
    """Average n noisy readings of a pose; circular mean on 4*yaw to
    handle the cube's 90-degree yaw symmetry / wrap at +-pi/4."""
    sx = sy = sz = 0.0
    s4 = c4 = 0.0
    for _ in range(n):
        p = robot.get_pose(name)
        pos = p["pos"]
        sx += pos[0]
        sy += pos[1]
        sz += pos[2]
        a = 4.0 * float(p.get("yaw", 0.0))
        s4 += math.sin(a)
        c4 += math.cos(a)
    yaw = math.atan2(s4, c4) / 4.0
    return sx / n, sy / n, sz / n, yaw


def _move(robot, x, y, z, yaw=None, speed=None):
    """move_to with targets clamped inside the safety box and
    MotionError caught so nothing can halt the skill."""
    x = _clamp(x, 0.05, 0.31)
    y = _clamp(y, -0.25, 0.25)
    z = _clamp(z, 0.015, 0.25)
    try:
        return robot.move_to(x, y, z, yaw=yaw, speed=speed)
    except Exception as exc:
        robot.log("move error", round(x, 3), round(y, 3), round(z, 3), exc)
        return None


def _pick(robot, name):
    for _ in range(4):
        x, y, _, yaw = _avg_pose(robot, name)
        robot.release()
        if _move(robot, x, y, 0.085, yaw=yaw) is None:
            continue
        if _move(robot, x, y, 0.015, yaw=yaw, speed=0.05) is None:
            _move(robot, x, y, 0.07, speed=0.1)
            continue
        robot.grasp()
        if robot.holding() == name:
            _move(robot, x, y, 0.11, speed=0.08)
            if robot.holding() == name:
                robot.log("picked", name)
                return True
        robot.release()
        _move(robot, x, y, 0.07, speed=0.1)
    robot.log("pick failed", name)
    return False


def _in_tray(robot, cube, tray):
    cx, cy, cz, _ = _avg_pose(robot, cube, n=4)
    tx, ty, _, _ = _avg_pose(robot, tray, n=4)
    dx = cx - tx
    dy = cy - ty
    inside = (dx * dx + dy * dy) < (0.035 * 0.035) and cz < 0.024
    robot.log("in_tray", cube, inside, round(dx, 3), round(dy, 3), round(cz, 3))
    return inside


def _place(robot, cube, tray):
    tx, ty, _, _ = _avg_pose(robot, tray)
    if _move(robot, tx, ty, 0.13) is None:
        return False
    if robot.holding() != cube:
        robot.log("lost in transport", cube)
        return False
    if _move(robot, tx, ty, 0.05, speed=0.08) is None:
        return False
    # lower the held cube into the tray (bottom ~1.3 cm above the floor,
    # below the 2.5 cm wall top) then release: minimal drop, no bounce
    _move(robot, tx, ty, 0.028, speed=0.05)
    robot.release()
    _move(robot, tx, ty, 0.12, speed=0.1)
    return _in_tray(robot, cube, tray)


def run(robot):
    robot.home()
    tasks = (("red_cube", "red_tray"), ("blue_cube", "blue_tray"))
    ok_all = True
    for cube, tray in tasks:
        done = False
        for _ in range(3):
            if _in_tray(robot, cube, tray):
                done = True
                break
            if robot.holding() != cube:
                if not _pick(robot, cube):
                    continue
            if _place(robot, cube, tray):
                done = True
                break
        if not done:
            ok_all = False
            robot.log("FAILED", cube, tray)
    robot.home()
    robot.log("finished, ok_all =", ok_all)
    return ok_all
