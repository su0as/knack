import math

def run(robot):
    """Pick up the red cube and hold it at least 5 cm above the table."""
    MAX_RETRIES = 3
    SAFE_Z = 0.065          # 6.5 cm above table -> meets the 5 cm clearance requirement
    ABOVE_OFFSET = 0.02     # unused but kept for clarity

    def safe_observe():
        """Return observation dict, retrying if red cube is missing due to occlusion."""
        for _ in range(MAX_RETRIES):
            obs = robot.observe()
            if "red_cube" in obs.get("objects", {}):
                return obs
            # If not visible, move the gripper a bit to the side and try again
            try:
                robot.move_by(dx=0.05, speed=0.1)
            except Exception:
                pass
        # Last attempt – return whatever we have (may still miss the cube)
        return robot.observe()

    def move_to_pose(target_pos, target_yaw=None, desc=""):
        """Move to a pose, handling MotionError with a single retry."""
        for attempt in range(2):
            try:
                res = robot.move_to(
                    target_pos[0],
                    target_pos[1],
                    target_pos[2],
                    yaw=target_yaw,
                    speed=0.05 if "approach" in desc.lower() else 0.1,
                )
                if res.get("ok", False):
                    return True
                # If not ok, treat as failure and maybe retry
            except Exception as e:  # MotionError or similar
                robot.log(f"Move failed ({desc}): {e}")
            # Small retreat and retry
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

    # Use actual observed cube height for grasp target
    cx, cy, cz = cube_info["pos"]
    grasp_pos = [cx, cy, cz]          # centre of the cube as observed
    cube_yaw = cube_info["yaw"]

    # Approach point: safely above the cube
    approach_pos = grasp_pos[:]
    approach_pos[2] = SAFE_Z          # fixed safe height for approach/lift

    # 1. Move to approach point (above cube)
    if not move_to_pose(approach_pos, cube_yaw, desc="approach"):
        robot.log("Failed to move to approach point.")
        return False

    # 2. Descend to grasp height (using actual cube height)
    if not move_to_pose(grasp_pos, cube_yaw, desc="descend"):
        robot.log("Failed to descend to grasp point.")
        return False

    # 3. Attempt to grasp (with a short retry)
    grasp_success = False
    for _ in range(2):
        robot.grasp()
        robot.wait(0.2)  # let grasp settle
        if robot.holding() == "red_cube":
            grasp_success = True
            break
        # grasp failed: retreat a bit, release, and try again
        robot.move_by(dz=ABOVE_OFFSET, speed=0.05)
        robot.release()
        robot.wait(0.1)

    if not grasp_success:
        robot.log("Grasp did not secure the red cube after retries.")
        return False

    # 4. Lift to safe height (>5 cm above table)
    lift_pos = grasp_pos[:]
    lift_pos[2] = SAFE_Z
    if not move_to_pose(lift_pos, cube_yaw, desc="lift"):
        robot.log("Failed to lift the cube.")
        return False

    # 5. Verify clearance; if too low, nudge upward
    obs_after = robot.observe()
    held_z = obs_after["objects"]["red_cube"]["pos"][2]
    if held_z < SAFE_Z - 0.0005:  # allow tiny tolerance
        robot.log(f"Cube low ({held_z:.4f}), nudging up.")
        robot.move_by(dz=0.002, speed=0.05)
        # re-check after nudge (optional)
        obs_after = robot.observe()
        held_z = obs_after["objects"]["red_cube"]["pos"][2]
        robot.log(f"After nudge: cube z = {held_z:.4f}")

    # Final success check
    if held_z >= SAFE_Z - 0.0005:
        robot.log("Red cube lifted and held >5 cm above table.")
        return True
    else:
        robot.log(f"Cube still too low ({held_z:.4f}) after corrective move.")
        return False
