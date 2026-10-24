import math


def _read_pose(robot, name, n=4):
    """Average several noisy pose readings."""
    xs, ys, zs, yaws = [], [], [], []
    for _ in range(n):
        p = robot.get_pose(name)
        xs.append(p["pos"][0])
        ys.append(p["pos"][1])
        zs.append(p["pos"][2])
        yaws.append(p["yaw"])
    return (sum(xs) / n, sum(ys) / n, sum(zs) / n, sum(yaws) / n)


def _try_move(robot, x, y, z, yaw=None, speed=None):
    try:
        r = robot.move_to(x, y, z, yaw=yaw, speed=speed)
        return bool(r.get("ok", False))
    except Exception:
        return False


def run(robot):
    target = "red_cube"

    robot.home()
    robot.release()

    # Small XY nudges used on retries in case the first grasp missed.
    offsets = [(0.0, 0.0), (0.008, 0.0), (-0.008, 0.0),
               (0.0, 0.008), (0.0, -0.008)]

    for attempt in range(5):
        try:
            x, y, z, yaw = _read_pose(robot, target, 4)
        except Exception:
            return False

        dx, dy = offsets[attempt % len(offsets)]
        tx = x + dx
        ty = y + dy

        robot.log("attempt", attempt, "target", tx, ty, yaw)

        # 1) Approach from above.
        if not _try_move(robot, tx, ty, 0.10, yaw=yaw, speed=0.15):
            if not _try_move(robot, tx, ty, 0.14, yaw=yaw, speed=0.15):
                robot.home()
                continue

        # 2) Descend slowly to the cube's mid-height.
        if not _try_move(robot, tx, ty, 0.016, yaw=yaw, speed=0.05):
            robot.home()
            continue

        # 3) Grasp and verify.
        grasped = robot.grasp()
        held = robot.holding()
        robot.log("grasp", grasped, "holding", held)

        if grasped and held == target:
            # 4) Lift well above the 5 cm requirement.
            _try_move(robot, tx, ty, 0.13, yaw=yaw, speed=0.08)
            if robot.holding() == target:
                _try_move(robot, tx, ty, 0.14, yaw=yaw, speed=0.08)
                if robot.holding() == target:
                    robot.log("success at attempt", attempt)
                    return True
            # Lost it during the lift — release and retry.
            robot.release()
        else:
            robot.release()

        robot.home()

    return False
