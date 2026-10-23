# Complete skill module
import math
import numpy as np
from collections import defaultdict

def run(robot):
    """
    Place each coloured cube into its matching coloured tray.
    The function returns True when the episode ends (success is verified by the
    simulator, not by this return value).
    """
    # ----------------------------------------------------------------------
    # 1. Perceive the scene
    # ----------------------------------------------------------------------
    obs = robot.observe()
    objects = obs["objects"]
    fixtures = obs["fixtures"]

    # ----------------------------------------------------------------------
    # 2. Build colour → (object, tray) mapping
    # ----------------------------------------------------------------------
    colour_to_obj = {name: data["color"] for name, data in objects.items()}
    # keep only tray fixtures (kind == "tray")
    colour_to_tray = {
        data["color"]: name for name, data in fixtures.items()
        if data["kind"] == "tray"
    }

    # ----------------------------------------------------------------------
    # 3. Process each colour that has both a cube and a tray
    # ----------------------------------------------------------------------
    for colour, obj_name in colour_to_obj.items():
        if colour not in colour_to_tray:
            continue                     # no matching tray, skip this colour
        tray_name = colour_to_tray[colour]

        obj_pose = robot.get_pose(obj_name)
        tray_pose = robot.get_pose(tray_name)

        # --------------------------------------------------------------
        # 3a. Move above the object to a safe height (3 cm)
        # --------------------------------------------------------------
        approach_x = obj_pose["pos"][0]
        approach_y = obj_pose["pos"][1]
        safe_height = 0.030               # a little higher than before
        try:
            robot.move_to(approach_x, approach_y, safe_height,
                          speed=0.07)
        except Exception:
            robot.log("move_to safe height failed – skipping this object")
            continue

        # --------------------------------------------------------------
        # 3b. Lower to grasp height, using the object's yaw for alignment
        # --------------------------------------------------------------
        grasp_z = 0.028
        try:
            robot.move_to(approach_x, approach_y, grasp_z,
                          yaw=obj_pose["yaw"], speed=0.07)
        except Exception:
            robot.log("move_to grasp height failed – skipping this object")
            continue

        robot.grasp()                     # close fingers
        # --------------------------------------------------------------
        # 3c. Verify grasp; if it failed, retry once with a larger lift
        # --------------------------------------------------------------
        if robot.holding() != obj_name:
            robot.log("grasp verification failed – retrying")
            try:
                # lift a bit more (≈0.025 m) and try again
                robot.move_to(approach_x, approach_y,
                              grasp_z + 0.025, speed=0.07)
                robot.grasp()
            except Exception:
                pass
            if robot.holding() != obj_name:
                robot.log(f"grasp still failed for {obj_name}")
                continue   # move on to the next colour

        # --------------------------------------------------------------
        # 3d. Move above the matching tray (use a slightly lower height)
        # --------------------------------------------------------------
        tray_x, tray_y, _ = tray_pose["pos"]
        release_above = 0.020             # 2 cm – gives clearance over tray edges
        try:
            robot.move_to(tray_x, tray_y, release_above,
                          speed=0.07)
        except Exception:
            robot.log("move_to above tray failed – skipping this object")
            continue

        # --------------------------------------------------------------
        # 3e. Descend to just above the tabletop and release the cube
        # --------------------------------------------------------------
        release_z = 0.015                 # 1.5 cm above the surface
        try:
            robot.move_to(tray_x, tray_y, release_z,
                          speed=0.07)
        except Exception:
            robot.log("final release move failed – skipping this object")
            continue

        robot.release()                   # open fingers to drop the cube
        robot.wait(0.3)                   # let the cube settle

    # ----------------------------------------------------------------------
    # 4. All known colour‑tray pairs have been attempted
    # ----------------------------------------------------------------------
    return True
