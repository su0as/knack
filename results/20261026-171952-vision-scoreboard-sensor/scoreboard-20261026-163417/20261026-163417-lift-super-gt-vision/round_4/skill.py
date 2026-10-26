import math

def run(robot):
    """Pick up the red cube and hold it at least 5 cm above the table."""
    MAX_RETRIES = 3
    SAFE_Z = 0.07          # 7 cm above table gives a margin over the 5 cm requirement
    TOL_Z = 0.005          # tolerance for verifying a move reached the target height
    GRASP_RETRY = 2
    LIFT_NUDGE = 0.01      # upward correction if cube ends up low
    NUDGE_ATTEMPTS = 2

    def safe_observe():
        """Return observation dict, retrying if red cube is missing due to occlusion."""
        for _ in range(MAX_RETRIES):
            obs = robot.observe()
            if "red_cube" in obs.get("objects", {}):
                return obs
            # Just try again; moving the gripper can invalidate later poses.
        # Last attempt – return whatever we have (may still miss the cube)
        return robot.observe()

    def move_and_check(target_pos, target_yaw=None, desc=""):
        """
        Attempt to move to target_pos, then verify the gripper's Z is within TOL_Z.
        Retries a couple of times on failure.
        """
        for attempt in range(2):
            try:
                # slower speed for precision motions
                speed = 0.05 if any(k in desc.lower() for k in ("approach", "descend", "lift")) else 0.1
                res = robot.move_to(
                    target_pos[0],
                    target_pos[1],
                    target_pos[2],
                    yaw=target_yaw,
                    speed=speed,
                )
                if not res.get("ok", False):
                    robot.log(f"Move not ok ({desc}), attempt {attempt+1}")
                    # small retreat before retry
                    robot.move_by(dz=-0.02, speed=0.05)
                    continue

                # Verify achieved height
                obs = robot.observe()
                grip_z = obs["gripper"]["pos"][2]
                if abs(grip_z - target_pos[2]) <= TOL_Z:
                    return True
                else:
                    robot.log(
                        f"Move {desc} gripper Z {grip_z:.4f} vs target {target_pos[2]:.4f} "
                        f"(diff {abs(grip_z - target_pos[2]):.4f}), attempt {attempt+1}"
                    )
                    # retreat and try again
                    robot.move_by(dz=-0.02, speed=0.05)
            except Exception as e:  # MotionError or similar
                robot.log(f"Move exception ({desc}): {e}")
                robot.move_by(dz=-0.02, speed=0.05)
        return False

    # Start from a known safe pose
    robot.home()

    # Get observation with retry for visibility
    obs = safe_observe()
    cube_info = obs["objects"].get("red_cube")
    if cube_info is None:
        robot.log("Red cube not perceived after retries.")
        return False

    cx, cy, cz = cube_info["pos"]
    cube_yaw = cube_info["yaw"]

    # Grasp target is the observed cube centre
    grasp_pos = [cx, cy, cz]

    # Approach point: safely above the cube
    approach_pos = [cx, cy, SAFE_Z]

    # 1. Move to approach point (above cube)
    if not move_and_check(approach_pos, cube_yaw, desc="approach"):
        robot.log("Failed to move to approach point.")
        return False

    # 2. Descend to grasp height (using actual cube height)
    if not move_and_check(grasp_pos, cube_yaw, desc="descend"):
        robot.log("Failed to descend to grasp point.")
        return False

    # 3. Attempt to grasp (with a short retry)
    grasp_success = False
    for _ in range(GRASP_RETRY):
        robot.grasp()
        robot.wait(0.2)  # let grasp settle
        if robot.holding() == "red_cube":
            grasp_success = True
            break
        # grasp failed: retreat a bit, release, and try again
        robot.move_by(dz=0.02, speed=0.05)
        robot.release()
        robot.wait(0.1)

    if not grasp_success:
        robot.log("Grasp did not secure the red cube after retries.")
        return False

    # 4. Lift to safe height (>5 cm above table)
    lift_pos = [cx, cy, SAFE_Z]
    if not move_and_check(lift_pos, cube_yaw, desc="lift"):
        robot.log("Failed to lift the cube.")
        return False

    # 5. Verify clearance; if too low, nudge upward
    for nudge_i in range(NUDGE_ATTEMPTS):
        obs_after = robot.observe()
        held_z = obs_after["objects"]["red_cube"]["pos"][2]
        if held_z >= SAFE_Z - TOL_Z:
            break  # sufficient height
        robot.log(f"Cube low ({held_z:.4f}), nudging up (attempt {nudge_i+1}).")
        robot.move_by(dz=LIFT_NUDGE, speed=0.05)
        robot.wait(0.1)  # let motion settle

    # Final check
    obs_final = robot.observe()
    final_z = obs_final["objects"]["red_cube"]["pos"][2]
    if final_z >= SAFE_Z - TOL_Z:
        robot.log(f"Red cube lifted and held >5 cm above table (z={final_z:.4f}).")
        return True
    else:
        robot.log(f"Cube still too low ({final_z:.4f}) after corrective moves.")
        return False
