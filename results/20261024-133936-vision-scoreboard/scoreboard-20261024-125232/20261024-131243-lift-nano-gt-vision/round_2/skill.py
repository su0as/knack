# skill module – improved version
import math
import numpy as np

def run(robot):
    """
    Pick up the red cube and hold it at least 5 cm above the table.
    Returns True if the lift appears successful, otherwise False.
    """

    # -------------------------------------------------
    # 1. Perceive the scene
    # -------------------------------------------------
    obs = robot.observe()
    if "red_cube" not in obs["objects"]:
        robot.log("red_cube missing in observation")
        return False

    # -------------------------------------------------
    # 2. Get a clean pose (reduces camera noise)
    # -------------------------------------------------
    pose = robot.get_pose("red_cube")          # {"pos": [...], "yaw": ...}
    x_obj, y_obj, z_obj = pose["pos"]
    yaw_obj = pose["yaw"]

    # -------------------------------------------------
    # 3. Parameters with safety margins
    # -------------------------------------------------
    PRE_GRASP_Z   = 0.07   # 7 cm above table – buffer for noise
    GRASP_Z       = 0.018  # just above the cube centre (~0.015 m)
    LIFT_TARGET_Z = 0.075  # 7.5 cm – guarantees ≥5 cm clearance

    # -------------------------------------------------
    # 4. Helper: safe move with optional fallback
    # -------------------------------------------------
    def try_move(x, y, z, yaw=None, speed=0.07, name=""):
        """Attempt a move_to; on failure try small reposition offsets."""
        try:
            return robot.move_to(x, y, z, yaw=yaw, speed=speed)
        except Exception as e:                     # MotionError or other
            robot.log(f"{name} move_to failed: {e}")
            # try a few small offsets (±1 cm) to stay inside reachable band
            for dx, dy in [(0.01, 0), (-0.01, 0), (0, 0.01), (0, -0.01)]:
                ok = robot.move_to(x + dx, y + dy, z, yaw=yaw, speed=speed)
                if ok["ok"]:
                    return ok
            return {"ok": False}

    # -------------------------------------------------
    # 5. Move to pre‑grasp height
    # -------------------------------------------------
    if not try_move(x_obj, y_obj, PRE_GRASP_Z, yaw=yaw_obj,
                    speed=0.07, name="pre‑grasp"):
        return False

    # -------------------------------------------------
    # 6. Descend to grasp height
    # -------------------------------------------------
    if not try_move(x_obj, y_obj, GRASP_Z, yaw=yaw_obj,
                    speed=0.07, name="grasp descend"):
        return False

    # -------------------------------------------------
    # 7. Close the fingers
    # -------------------------------------------------
    if not robot.grasp():
        robot.log("grasp() failed – retrying")
        # lift a bit and re‑approach from a slightly different angle
        if not try_move(x_obj, y_obj, PRE_GRASP_Z + 0.01, yaw=yaw_obj,
                        speed=0.07, name="grasp retry approach"):
            return False
        if not try_move(x_obj, y_obj, GRASP_Z, yaw=yaw_obj,
                        speed=0.07, name="grasp retry descend"):
            return False
        if not robot.grasp():
            robot.log("grasp() failed again – abort")
            return False

    # -------------------------------------------------
    # 8. Verify that the cube is actually held
    # -------------------------------------------------
    if robot.holding() != "red_cube":
        robot.log("holding check failed")
        return False

    # -------------------------------------------------
    # 9. Lift to the required height (≥5 cm)
    # -------------------------------------------------
    if not try_move(x_obj, y_obj, LIFT_TARGET_Z, yaw=yaw_obj,
                    speed=0.07, name="lift"):
        return False

    robot.log("red_cube lifted to required height")
    return True
