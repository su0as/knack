# --------------------------------------------------------------
#  Sort‑by‑colour skill – first version
# --------------------------------------------------------------
def run(robot):
    """
    Main entry point for the skill.  It must return True if the
    task appears successful, otherwise False.  The function runs
    on a freshly randomised scene each episode.
    """

    # ------------------------------------------------------------------
    # Helper: safe move with error handling
    # ------------------------------------------------------------------
    def safe_move_to(x, y, z, yaw=None, speed=None):
        """Move tool point to (x,y,z) with optional orientation and speed."""
        try:
            result = robot.move_to(x, y, z, yaw=yaw, speed=speed)
            # The safety layer may clamp values; we just trust the result.
            return result
        except MotionError:
            # If the target is unreachable, signal failure to the caller.
            return {"ok": False, "pos": None, "error_m": None}

    # ------------------------------------------------------------------
    # Helper: pick an object by name
    # ------------------------------------------------------------------
    def pick(obj_name, max_retries=3):
        """
        Approach, grasp and lift the named object.
        Returns the gripper pose (x,y,yaw) on success, otherwise False.
        """
        # 1. Get a fresh perception snapshot
        obs = robot.observe()
        if obj_name not in obs["objects"]:
            return False
        obj = obs["objects"][obj_name]
        ox, oy, oz = obj["pos"]
        oyaw = obj["yaw"]

        # 2. Move to a pre‑grasp pose a little above the object
        pre_z = 0.025                     # 2.5 cm above the table
        move_res = safe_move_to(ox, oy, pre_z, yaw=oyaw, speed=0.07)
        if not move_res["ok"]:
            return False

        # 3. Lower to the grasp height (cube centre ≈ 0.015 m)
        move_res = safe_move_to(ox, oy, 0.015, yaw=oyaw, speed=0.05)
        if not move_res["ok"]:
            return False

        # 4. Close the fingers
        if not robot.grasp():
            # Simple retry: lift a touch, re‑lower and try again
            robot.release()
            move_res = safe_move_to(ox, oy, 0.015, yaw=oyaw, speed=0.05)
            if not move_res["ok"] or not robot.grasp():
                return False

        # 5. Lift the object clear of the surface
        lift_z = 0.05                     # 5 cm above the table
        safe_move_to(ox, oy, lift_z, yaw=oyaw, speed=0.07)

        # Return the current pose for later placement
        return (ox, oy, oyaw)

    # ------------------------------------------------------------------
    # Helper: place an held object into a tray
    # ------------------------------------------------------------------
    def place_into_tray(tray_name, grip_pose):
        """
        Move the gripper above the centre of the given tray,
        lower to grasp height, release, then lift away.
        """
        # 1. Retrieve the tray centre (noise‑free enough for planning)
        tray_pose = robot.get_pose(tray_name)
        tx, ty, _ = tray_pose["pos"]

        # 2. Approach from above
        move_res = safe_move_to(tx, ty, 0.025, speed=0.07)
        if not move_res["ok"]:
            return False

        # 3. Lower to the release height (just above the table)
        move_res = safe_move_to(tx, ty, 0.015, speed=0.05)
        if not move_res["ok"]:
            return False

        # 4. Release the object
        robot.release()

        # 5. Lift away to avoid dragging
        x, y, yaw = grip_pose
        safe_move_to(x, y, 0.05, yaw=yaw, speed=0.07)

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
