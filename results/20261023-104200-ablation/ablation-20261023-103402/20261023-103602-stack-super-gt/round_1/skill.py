import math

def run(robot):
    """Stack the red cube on top of the blue cube."""
    MAX_RETRIES = 2
    SAFE_Z = 0.15          # safe travel height
    APPROACH_Z_OFFSET = 0.05  # distance above cube for pre‑grasp
    GRASP_SPEED = 0.08     # slow near objects
    TRAVEL_SPEED = 0.15    # default speed for longer moves

    def get_cube_pose(name):
        """Return pose dict for a cube, using observe() first then get_pose() as fallback."""
        obs = robot.observe()
        if name in obs["objects"]:
            return obs["objects"][name]
        # fallback (should rarely be needed)
        return robot.get_pose(name)

    def move_to_pose(x, y, z, yaw=None, speed=TRAVEL_SPEED, desc=""):
        """Wrapper that catches MotionError and logs."""
        try:
            res = robot.move_to(x, y, z, yaw=yaw, speed=speed)
            if not res["ok"]:
                robot.log(f"Move blocked ({desc}): {res}")
                return False
            return True
        except Exception as e:  # MotionError is an Exception
            robot.log(f"MotionError during {desc}: {e}")
            return False

    def grasp_cube(cube_pose):
        """Attempt to grasp the cube; returns True if successful."""
        cx, cy, cz = cube_pose["pos"]
        cyaw = cube_pose["yaw"]

        # Pre‑grasp pose: above the cube
        pre_z = cz + APPROACH_Z_OFFSET
        if not move_to_pose(cx, cy, pre_z, yaw=cyaw, speed=GRASP_SPEED, desc="pre‑grasp"):
            return False

        # Descend to grasp height (around cube centre)
        grasp_z = cz  # finger pads around middle of cube
        if not move_to_pose(cx, cy, grasp_z, yaw=cyaw, speed=GRASP_SPEED, desc="descend to grasp"):
            return False

        # Close fingers
        if not robot.grasp():
            robot.log("Grasp failed (no object detected)")
            # Retreat a bit to avoid collision
            robot.move_by(dz=0.02, speed=GRASP_SPEED)
            return False

        # Verify hold
        if robot.holding() is None:
            robot.log("Grasp returned True but holding() is None")
            robot.release()
            robot.move_by(dz=0.02, speed=GRASP_SPEED)
            return False

        robot.log(f"Successfully grasped {robot.holding()}")
        # Lift up
        robot.move_by(dz=SAFE_Z - grasp_z, speed=TRAVEL_SPEED)
        return True

    # -----------------------------------------------------------------
    # Main stacking routine
    # -----------------------------------------------------------------
    for attempt in range(MAX_RETRIES + 1):
        # 1. Observe and get poses
        red_pose = get_cube_pose("red_cube")
        blue_pose = get_cube_pose("blue_cube")

        rx, ry, rz = red_pose["pos"]
        ryaw = red_pose["yaw"]
        bx, by, bz = blue_pose["pos"]
        byaw = blue_pose["yaw"]

        # 2. Grasp red cube
        if not grasp_cube(red_pose):
            robot.log(f"Attempt {attempt+1}: failed to grasp red cube, retrying...")
            robot.home()
            continue

        # 3. Move above blue cube (safe height)
        above_z = bz + SAFE_Z  # keep same safe Z offset
        if not move_to_pose(bx, by, above_z, yaw=byaw, speed=TRAVEL_SPEED, desc="move above blue"):
            robot.log("Failed to move above blue cube")
            robot.release()
            robot.home()
            return False

        # 4. Lower to stacking height: red centre should be at blue centre + cube height
        stack_z = bz + 0.03  # cube height = 0.03 m
        if not move_to_pose(bx, by, stack_z, yaw=byaw, speed=GRASP_SPEED, desc="lower to stack"):
            robot.log("Failed to lower onto blue cube")
            robot.release()
            robot.move_by(dz=SAFE_Z - stack_z, speed=TRAVEL_SPEED)
            robot.home()
            return False

        # 5. Release red cube
        robot.release()
        robot.log("Released red cube onto blue cube")

        # 6. Retreat upward
        robot.move_by(dz=SAFE_Z - stack_z, speed=TRAVEL_SPEED)

        # 7. Final check: red cube should now be above blue cube
        # (optional verification – we can observe again)
        obs = robot.observe()
        if obs["gripper"]["holding"] is None:
            robot.log("Stack completed successfully.")
            return True
        else:
            robot.log("Still holding something after release – unexpected.")
            robot.home()
            return False

    # If we exhausted retries without success
    robot.log("Exceeded max attempts for stacking.")
    robot.home()
    return False
