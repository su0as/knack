"""Hand-written reference skills. TEST FIXTURES ONLY.

They prove each scene is solvable through the public robot API (physics, IK,
grasping, success checks). They are NEVER shown to the coding agent; a unit
test asserts that no prompt contains them. Knack's claim of zero demonstrations
refers to the agent loop, which starts from the task text and the API doc only.
"""

PICK = '''
def pick(robot, name):
    c = robot.get_pose(name)
    x, y, z = c["pos"]
    yaw = c["yaw"]
    robot.release()
    robot.move_to(x, y, 0.08, yaw=yaw)
    robot.move_to(x, y, 0.016, yaw=yaw, speed=0.08)
    ok = robot.grasp()
    robot.move_to(x, y, 0.09, yaw=yaw)
    return ok, yaw


def place_at(robot, x, y, z_release, yaw):
    robot.move_to(x, y, 0.09, yaw=yaw)
    robot.move_to(x, y, z_release, yaw=yaw, speed=0.08)
    robot.release()
    robot.move_to(x, y, 0.09, yaw=yaw)
'''

ORACLES = {
    "lift": PICK + '''
def run(robot):
    ok, yaw = pick(robot, "red_cube")
    p = robot.get_pose("red_cube")["pos"]
    robot.move_to(p[0], p[1], 0.11, yaw=yaw)
    return ok
''',
    "place": PICK + '''
def run(robot):
    ok, yaw = pick(robot, "blue_cube")
    if not ok:
        return False
    t = robot.get_pose("target")["pos"]
    place_at(robot, t[0], t[1], 0.02, yaw)
    return True
''',
    "stack": PICK + '''
def run(robot):
    ok, yaw = pick(robot, "red_cube")
    if not ok:
        return False
    b = robot.get_pose("blue_cube")
    bx, by, bz = b["pos"]
    place_at(robot, bx, by, bz + 0.032, b["yaw"])
    return True
''',
    "tray": PICK + '''
def run(robot):
    ok, yaw = pick(robot, "yellow_cube")
    if not ok:
        return False
    t = robot.get_pose("tray")["pos"]
    place_at(robot, t[0], t[1], 0.05, yaw)
    return True
''',
    "sort": PICK + '''
def run(robot):
    done = True
    for cube, tray in (("red_cube", "red_tray"), ("blue_cube", "blue_tray")):
        ok, yaw = pick(robot, cube)
        if not ok:
            done = False
            continue
        t = robot.get_pose(tray)["pos"]
        place_at(robot, t[0], t[1], 0.05, yaw)
    return done
''',
    "push": '''
import math


def run(robot):
    for attempt in range(3):
        p = robot.get_pose("puck")["pos"]
        t = robot.get_pose("target")["pos"]
        dx, dy = t[0] - p[0], t[1] - p[1]
        d = math.hypot(dx, dy)
        if d < 0.012:
            break
        ux, uy = dx / d, dy / d
        yaw = math.atan2(uy, ux) + math.pi / 2  # fingers spread across the push direction
        sx, sy = p[0] - ux * 0.065, p[1] - uy * 0.065
        robot.move_to(sx, sy, 0.06, yaw=yaw)
        robot.grasp()  # closed fingers make a solid paddle (open fingers wedge the puck and tip it)
        robot.move_to(sx, sy, 0.016, yaw=yaw, speed=0.08)
        # paddle face is ~1 cm ahead of the tool point, puck radius 3 cm
        ex, ey = t[0] - ux * 0.04, t[1] - uy * 0.04
        robot.move_to(ex, ey, 0.016, yaw=yaw, speed=0.05)
        robot.move_to(ex - ux * 0.03, ey - uy * 0.03, 0.016, yaw=yaw, speed=0.05)
        robot.move_to(ex - ux * 0.03, ey - uy * 0.03, 0.07, yaw=yaw)
    return True
''',
}

# A deliberately broken first attempt, used by the offline mock coder.
BROKEN = '''
def run(robot):
    obs = robot.observe()
    cube = obs["objects"]["red_cube"]
    robot.move_to(cube["pos"][0], cube["pos"][1], 0.0)
    robot.grasp()
    return True
'''
