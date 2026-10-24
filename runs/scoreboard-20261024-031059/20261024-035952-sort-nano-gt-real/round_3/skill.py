# --------------------------------------------------------------
#  Sort‑by‑colour skill – improved version (Round 2 fixes)
# --------------------------------------------------------------
import math
import numpy as np  # allowed import

# ------------------------------------------------------------------
# Exception raised by the safety layer when a move is unreachable
# ------------------------------------------------------------------
class MotionError(Exception):
    pass


def run(robot):
    """
    Main entry point for the skill. Returns True if the task appears successful,
    otherwise False. Runs on a freshly randomised scene each episode.
    """

    # ------------------------------------------------------------------
    # Workspace limits (strict safety bounds)
    # ------------------------------------------------------------------
    SAFE_X = (0.04, 0.32)
    SAFE_Y = (-0.26, 0.26)
    SAFE_Z = (0.014, 0.26)

    def clamp_coord(val, limits):
        lo, hi = limits
        return max(lo, min(hi, val))

    # ------------------------------------------------------------------
    # Helper: safe move with error handling and workspace clamping
    # ------------------------------------------------------------------
    def safe_move_to(x, y, z, yaw=None, speed=None):
        """Move tool point to (x,y,z) with optional orientation and speed."""
        # Clamp to the strict workspace limits to avoid safety halts
        x = clamp_coord(x, SAFE_X)
        y = clamp_coord(y, SAFE_Y)
        z = clamp_coord(z, SAFE_Z)

        try:
            result = robot.move_to(x, y, z, yaw=yaw, speed=speed)
            return result
        except MotionError:
            # Target unreachable – signal failure to caller
            return {"ok": False, "pos": None, "error_m": None}

    # ------------------------------------------------------------------
    # Helper: pick an object by name
    # ------------------------------------------------------------------
    def pick(obj_name, max_retries=3):
        """
        Approach, grasp and lift the named object.
        Returns the gripper pose (x, y, yaw) on success, otherwise False.
        """
        for attempt in range(max_retries):
            # 1. Fresh perception snapshot
            obs = robot.observe()
            if obj_name not in obs["objects"]:
                return False
            obj = obs["objects"][obj_name]
            ox, oy, oz = obj["pos"]
            oyaw = obj["yaw"]

            # 2. Small pause to let the simulated scene settle
            robot.wait(0.1)

            # 3. Pre‑grasp pose a little above the object
            pre_z = 0.025                     # 2.5 cm above table
            move_res = safe_move_to(ox, oy, pre_z, yaw=oyaw, speed=0.07)
            if not move_res["ok"]:
                return False

            # 4. Lower to grasp height (cube centre ≈ 0.015 m)
            move_res = safe_move_to(ox, oy, 0.015, yaw=oyaw, speed=0.05)
            if not move_res["ok"]:
                return False

            # 5. Close the fingers
            if not robot.grasp():
                # Simple retry: lift a bit, re‑lower and try again
                robot.release()
                move_res = safe_move_to(ox, oy, 0.015, yaw=oyaw, speed=0.05)
                if not move_res["ok"] or not robot.grasp():
                    return False

            # 6. Verify that the object is actually held
            if robot.holding() != obj_name:
                # Drop any loosely held object and retry
                robot.release()
                continue

            # 7. Lift clear of the surface
            lift_z = 0.05                     # 5 cm above table
            safe_move_to(ox, oy, lift_z, yaw=oyaw, speed=0.07)

            # Return the current pose for later placement
            return (ox, oy, oyaw)

        # Exhausted retries
        return False

    # ------------------------------------------------------------------
    # Helper: place an held object into a tray
    # ------------------------------------------------------------------
    def place_into_tray(tray_name, grip_pose):
        """
        Move the gripper above the centre of the given tray,
        lower to release height, release, then lift away.
        """
        # 1. Get tray centre (fresh pose)
        tray_pose = robot.get_pose(tray_name)
        tx, ty, _ = tray_pose["pos"]

        # 2. Approach from a safe height above the tray (clear of rim)
        approach_z = 0.045          # 4.5 cm – clears the cube and tray rim
        move_res = safe_move_to(tx, ty, approach_z, speed=0.07)
        if not move_res["ok"]:
            return False

        # 3. Lower to release height (just above the table)
        release_z = 0.025           # 2.5 cm – enough to clear the cube centre
        move_res = safe_move_to(tx, ty, release_z, speed=0.05)
        if not move_res["ok"]:
            return False

        # 4. Release the object
        robot.release()

        # 5. Lift away to avoid dragging; use a fresh safe height
        lift_z = 0.05               # 5 cm above table
        safe_move_to(tx, ty, lift_z, speed=0.07)

        return True

    # ------------------------------------------------------------------
    # Main execution: process the two cubes in order
    # ------------------------------------------------------------------
    # 1. Pick the red cube and place it into the red tray
    grip_pose = pick("red_cube")
    if not grip_pose:
        return False
    if not place_into_tray("red_tray", grip_pose):
        return False

    # 2. Pick the blue cube and place it into the blue tray
    grip_pose = pick("blue_cube")
    if not grip_pose:
        return False
    if not place_into_tray("blue_tray", grip_pose):
        return False

    # All steps completed successfully
    return True
