# Complete skill module
import math
import numpy as np
from collections import defaultdict

def run(robot):
    """
    Place each coloured cube into its matching coloured tray.
    Returns True when the episode ends (success is verified by the simulator).
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
        # 3a. Move above the object to a safe height (now 0.035 m)
        # --------------------------------------------------------------
        safe_height = 0.035
        try:
            robot.move_to(obj_pose["pos"][0], obj_pose["pos"][1],
                          safe_height, speed=0.07)
        except Exception:
            robot.log("move_to safe height failed – skipping")
            continue

        # --------------------------------------------------------------
        # 3b. Lower to grasp height (now 0.033 m) using the object's yaw
        # --------------------------------------------------------------
        grasp_z = 0.033                     # +0.005 m from previous version
        try:
            robot.move_to(obj_pose["pos"][0], obj_pose["pos"][1],
                          grasp_z, yaw=obj_pose["yaw"], speed=0.07)
        except Exception:
            robot.log("move_to grasp height failed – skipping")
            continue

        robot.grasp()

        # --------------------------------------------------------------
        # 3c. Verify grasp; if it failed, retry once with a larger lift
        # --------------------------------------------------------------
        if robot.holding() != obj_name:
            robot.log("grasp verification failed – retrying")
            try:
                # lift a bit more (≈0.040 m) and try again
                robot.move_to(obj_pose["pos"][0], obj_pose["pos"][1],
                              grasp_z + 0.040, speed=0.07)
                robot.grasp()
            except Exception:
                pass
            if robot.holding() != obj_name:
                robot.log(f"grasp still failed for {obj_name}")
                continue

        # --------------------------------------------------------------
        # 3d. Post‑grasp lift check – raise a little to lock the grip
        # --------------------------------------------------------------
        lift_z = grasp_z + 0.030               # increased from 0.01 m
        try:
            robot.move_to(obj_pose["pos"][0], obj_pose["pos"][1],
                          lift_z, speed=0.07)
            if robot.holding() != obj_name:
                robot.log("lift lost grip – aborting this colour")
                continue
        except Exception:
            robot.log("lift move failed – aborting this colour")
            continue

        # --------------------------------------------------------------
        # 3e. Move above the matching tray (slow speed for centering)
        # --------------------------------------------------------------
        tray_x, tray_y, _ = tray_pose["pos"]
        release_above = 0.020                 # 2 cm clearance over tray edges
        try:
            robot.move_to(tray_x, tray_y, release_above, speed=0.05)
        except Exception:
            robot.log("move_to above tray failed – skipping")
            continue

        # --------------------------------------------------------------
        # 3f. Final centering move (same target, slower) – ensures centre over tray
        # --------------------------------------------------------------
        try:
            robot.move_to(tray_x, tray_y, 0.020, speed=0.05)
        except Exception:
            robot.log("centering move failed – skipping")
            continue

        # --------------------------------------------------------------
        # 3g. Corrective centering – ensure exact centre over tray before release
        # --------------------------------------------------------------
        try:
            robot.move_to(tray_x, tray_y, 0.020, speed=0.05)
        except Exception:
            robot.log("corrective centering failed – skipping")
            continue

        # --------------------------------------------------------------
        # 3h. Descend to just above the tabletop and release the cube
        # --------------------------------------------------------------
        release_z = 0.015                     # 1.5 cm above surface
        try:
            robot.move_to(tray_x, tray_y, release_z, speed=0.07)
        except Exception:
            robot.log("final release move failed – skipping")
            continue

        robot.release()                       # open fingers to drop the cube
        robot.wait(0.3)                       # let the cube settle

    # ----------------------------------------------------------------------
    # 4. All known colour‑tray pairs have been attempted
    # ----------------------------------------------------------------------
    return True
