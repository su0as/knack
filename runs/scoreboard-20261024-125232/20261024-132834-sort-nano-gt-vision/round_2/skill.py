# skill module – improved version
# -------------------------------------------------
# Allowed imports
import math
import numpy as np
from collections import defaultdict

# -------------------------------------------------
def run(robot):
    """
    Main skill entry point.
    Returns True if both cubes are successfully placed in their matching trays,
    otherwise False.
    """

    # ---------- 1. Perceive ----------
    obs = robot.observe()
    objs = obs.get('objects', {})
    fixtures = obs.get('fixtures', {})

    # Identify cubes and trays by colour
    red_cube = objs.get('red_cube')
    blue_cube = objs.get('blue_cube')
    red_tray = fixtures.get('red_tray')
    blue_tray = fixtures.get('blue_tray')

    if not (red_cube and blue_cube and red_tray and blue_tray):
        robot.log("Missing required objects or fixtures")
        return False

    # ---------- 2. Helper: pick‑and‑place ----------
    def pick_and_place(obj_name, tray_name):
        """Pick a single object and deposit it in its matching tray."""
        obj = objs[obj_name]
        tray = fixtures[tray_name]

        # ---- approach above the object (lift a bit) ----
        approach = list(obj['pos'])          # [x, y, z]
        approach[2] += 0.005                 # ~5 mm above the centre
        yaw_angle = obj.get('yaw', 0.0)      # align fingers with object faces

        try:
            robot.move_to(approach[0], approach[1], approach[2], yaw=yaw_angle,
                          speed=0.07)
        except Exception as e:               # MotionError or other reachability issue
            robot.log("move_to (approach) failed:", e)
            return False

        # ---- close the gripper ----
        if not robot.grasp():
            robot.log("grasp failed, retrying")
            if not robot.grasp():
                return False

        # ---- verify that the object is held ----
        if robot.holding() != obj_name:
            robot.log("hold verification failed – retrying grasp")
            if not robot.grasp():
                return False

        # ---- move above the tray centre (clearance hover) ----
        place_target = list(tray['pos'])     # [x, y, z] of tray centre (z == 0)
        clearance = 0.020                    # 2 cm hover above the tray
        release_height = place_target[2] + 0.005  # ~5 mm above table for release

        # 1) Hover high enough to clear the tray
        try:
            robot.move_to(place_target[0], place_target[1],
                          place_target[2] + clearance, speed=0.07)
        except Exception as e:
            robot.log("move_to (pre‑place hover) failed:", e)
            return False

        # 2) Descend to release height
        try:
            robot.move_to(place_target[0], place_target[1], release_height,
                          speed=0.07)
        except Exception as e:
            robot.log("move_to (release height) failed:", e)
            return False

        # ---- release the object ----
        robot.release()

        # ---- retract clear of the tray before waiting ----
        try:
            robot.move_to(place_target[0], place_target[1],
                          place_target[2] + clearance, speed=0.07)
        except Exception as e:
            robot.log("move_to (retract after release) failed:", e)
            return False

        robot.wait(0.3)                     # give time for the object to settle
        return True

    # ---------- 3. Execute the two pick‑and‑place actions ----------
    if not pick_and_place('red_cube', 'red_tray'):
        return False
    if not pick_and_place('blue_cube', 'blue_tray'):
        return False

    # ---------- 4. Success ----------
    return True
