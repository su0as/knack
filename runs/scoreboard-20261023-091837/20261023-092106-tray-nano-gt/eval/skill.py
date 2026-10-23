# skill module – first version: put the yellow cube into the tray and let go
import math, numpy as np, itertools, functools, collections

def run(robot):
    """
    Main skill entry point. Returns True if the yellow cube ends up in the tray,
    False otherwise. The function is called repeatedly with a fresh randomised
    scene each episode.
    """

    # ----------------------------------------------------------------------
    # Configuration (tunable but kept simple for the first iteration)
    # ----------------------------------------------------------------------
    APPROACH_SPEED = 0.07   # m/s for moving near objects
    PLACE_SPEED    = 0.05   # slower speed when positioning for release
    MAX_RETRIES    = 3      # how many times we retry a failed step
    CUBE_HEIGHT    = 0.015  # z‑position of a cube’s centre (approx.)

    # ----------------------------------------------------------------------
    # Helper: fetch the current 3‑D pose of a named object/fixture
    # ----------------------------------------------------------------------
    def pose(name):
        """Return [x, y, z] of the named object/fixture (ignoring orientation)."""
        return robot.get_pose(name)['pos']

    # ----------------------------------------------------------------------
    # 1️⃣  Pick up the yellow cube
    # ----------------------------------------------------------------------
    for attempt in range(MAX_RETRIES):
        try:
            obs = robot.observe()
            cube = obs['objects']['yellow_cube']
            cx, cy, _ = cube['pos']               # centre of the cube

            # ---- move above the cube (safe height) ----
            above_z = 0.12                          # a height well inside the reachable workspace
            ok, _, _ = robot.move_to(cx, cy, above_z, speed=APPROACH_SPEED)
            if not ok:
                raise RuntimeError('move_to above cube failed')

            # ---- descend to the cube’s centre ----
            ok, _, _ = robot.move_to(cx, cy, CUBE_HEIGHT, speed=PLACE_SPEED)
            if not ok:
                raise RuntimeError('move_to cube centre failed')

            # ---- close fingers and verify hold ----
            if not robot.grasp():
                raise RuntimeError('grasp() returned False')
            if robot.holding() != 'yellow_cube':
                raise RuntimeError('not holding the yellow cube')
            break   # success, exit retry loop
        except Exception as e:
            # If we have exhausted retries, report failure; otherwise wait and try again
            if attempt == MAX_RETRIES - 1:
                robot.log('failed to pick up yellow cube')
                return False
            robot.log('pick retry', e)
            robot.wait(0.2)

    # ----------------------------------------------------------------------
    # 2️⃣  Transport the cube to the tray and release it
    # ----------------------------------------------------------------------
    for attempt in range(MAX_RETRIES):
        try:
            obs = robot.observe()
            tray = obs['fixtures']['tray']
            tx, ty, _ = tray['pos']               # centre of the tray

            # ---- move above the tray centre ----
            above_z = 0.12
            ok, _, _ = robot.move_to(tx, ty, above_z, speed=APPROACH_SPEED)
            if not ok:
                raise RuntimeError('move_to above tray failed')

            # ---- lower to a release height just above the tray surface ----
            ok, _, _ = robot.move_to(tx, ty, CUBE_HEIGHT, speed=PLACE_SPEED)
            if not ok:
                raise RuntimeError('move_to release height failed')

            # ---- open gripper to let the cube drop into the tray ----
            robot.release()

            # ---- verify that the cube is no longer held ----
            if robot.holding() is not None:
                # Something went wrong; retry the whole release step
                robot.log('still holding after release, retrying')
                robot.wait(0.2)
                continue

            # ---- success: object is in the tray and released ----
            return True
        except Exception as e:
            # Any unexpected error aborts the skill; log and report failure
            robot.log('error during transport/release', e)
            if attempt == MAX_RETRIES - 1:
                return False
            robot.wait(0.2)

    # If we exit the loop without returning, something failed
    return False
