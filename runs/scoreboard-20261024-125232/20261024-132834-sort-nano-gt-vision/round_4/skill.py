# skill module – updated version
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

    red_cube = objs.get('red_cube')
    blue_cube = objs.get('blue_cube')
    red_tray = fixtures.get('red_tray')
    blue_tray = fixtures.get('blue_tray')

    if not (red_cube and blue_cube and red_tray and blue_tray):
        robot.log("Missing required objects or fixtures")
        return False

    # ---------- 2. Helper: safe move with retry ----------
    def safe_move(x, y, z, yaw=None, speed=0.07, max_trials=2):
        """
        Attempt robot.move_to with limited retries.
        If the motion stops short, reduce speed and lower z slightly,
        then try again (up to max_trials).
        Returns True on success, False otherwise.
        """
        cur_z = z
        for trial in range(max_trials):
            try:
                result = robot.move_to(x, y, z, yaw=yaw, speed=speed)
            except Exception as e:
                robot.log("move_to exception:", e)
                return False

            if result["ok"]:
                return True

            # motion stopped short – log and adjust for next trial
            robot.log(
                f"move_to stopped short (trial {trial+1}), note={result.get('note')}"
            )
            # reduce speed but keep it above the safety minimum
            speed = max(0.04, speed * 0.5)
            # lower the target a bit more to clear the obstacle
            cur_z -= 0.005
            z = cur_z
        robot.log("move_to failed after retries")
        return False

    # ---------- 3. Pick‑and‑place routine ----------
    def pick_and_place(obj_name, tray_name):
        """Pick a single object and deposit it in its matching tray."""
        obj = objs[obj_name]
        tray = fixtures[tray_name]

        # ---- approach above the object (lift a bit) ----
        approach = list(obj['pos'])
        approach[2] += 0.005                     # ~5 mm above centre
        yaw_angle = obj.get('yaw', 0.0)

        if not safe_move(*approach, yaw=yaw_angle, speed=0.07):
            return False

        # ---- first grasp attempt ----
        if not robot.grasp():
            robot.log("grasp failed, retrying")
            # shake‑off: lift slightly then lower again
            shake = list(obj['pos'])
            shake[2] += 0.01
            if not safe_move(*shake, speed=0.05):
                return False
            if not robot.grasp():
                robot.log("grasp after shake failed")
                return False
            # after shake we must be holding the object
            if robot.holding() != obj_name:
                robot.log("still not holding after shake")
                return False

        # ---- verify hold (should be true now) ----
        if robot.holding() != obj_name:
            robot.log("hold verification failed")
            return False

        # ---- hover above the tray centre (clearance) ----
        clearance = 0.020                         # 2 cm above tray
        if not safe_move(
            tray['pos'][0], tray['pos'][1],
            tray['pos'][2] + clearance, speed=0.07
        ):
            return False

        # ---- descend to release height (just above table) ----
        release_z = tray['pos'][2] + 0.005        # ~5 mm above tabletop
        if not safe_move(
            tray['pos'][0], tray['pos'][1], release_z,
            speed=0.04
        ):
            return False

        # ---- release the object ----
        robot.release()

        # ---- micro‑adjust: nudge cube into tray before retracting ----
        if not safe_move(
            tray['pos'][0], tray['pos'][1],
            tray['pos'][2] + 0.001, speed=0.03
        ):
            return False

        # ---- retract to clearance before waiting ----
        if not safe_move(
            tray['pos'][0], tray['pos'][1],
            tray['pos'][2] + clearance, speed=0.07
        ):
            return False

        robot.wait(0.3)                           # let the cube settle
        return True

    # ---------- 4. Execute the two pick‑and‑place actions ----------
    if not pick_and_place('red_cube', 'red_tray'):
        return False
    if not pick_and_place('blue_cube', 'blue_tray'):
        return False

    # ---------- 5. Success ----------
    return True
