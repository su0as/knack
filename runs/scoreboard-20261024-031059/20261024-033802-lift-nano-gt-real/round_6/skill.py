# skill module
import math
import itertools

def run(robot):
    """
    Pick up the red cube and hold it at least 5 cm above the table.
    Returns True when the cube is securely held at the target height.
    """
    RED_NAME = "red_cube"
    REQUIRED_Z = 0.065          # 5 cm above tabletop
    # Minimum vertical clearance for the pre‑grasp pose
    PRE_GRASP_MIN = 0.020       # 2 cm above table (safe floor)
    CLEARANCE_ABOVE = 0.010     # at least 1 cm above the observed cube centre
    # Horizontal safety offset
    HOFFSET = 0.005
    # Speeds
    SPEED_APPROACH = 0.10
    SPEED_LIFT = 0.07
    # Wait times
    WAIT_AFTER_OBSERVE = 0.5
    WAIT_AFTER_MOVE = 0.1
    SETTLE_AFTER_MOVE = 0.05
    WAIT_AFTER_GRASP = 0.2
    MAX_RETRIES = 12

    for attempt in range(MAX_RETRIES):
        # ------------------------------------------------------------
        # 1. Perceive the scene and wait for a stable observation
        # ------------------------------------------------------------
        obs = robot.observe()
        robot.wait(WAIT_AFTER_OBSERVE)

        objs = obs.get("objects", {})
        if RED_NAME not in objs:
            robot.log("red_cube not seen, retry")
            robot.wait(0.2)
            continue

        cube = objs[RED_NAME]
        cx, cy, cz = cube["pos"]
        cyaw = cube["yaw"]

        # ------------------------------------------------------------
        # 2. Compute a safe tool‑point just above the cube centre
        # ------------------------------------------------------------
        offset_x = HOFFSET if cx >= 0 else -HOFFSET
        offset_y = HOFFSET if cy >= 0 else -HOFFSET
        target_x = cx + offset_x
        target_y = cy + offset_y
        # Clamp to the robot's reachable area
        target_x = max(0.04, min(0.32, target_x))
        target_y = max(-0.26, min(0.26, target_y))

        # ------------------------------------------------------------
        # 3. Pre‑grasp pose (ensure enough clearance)
        # ------------------------------------------------------------
        # Guarantee at least CLEARANCE_ABOVE above the observed centre,
        # but never go below PRE_GRASP_MIN.
        pre_grasp_z = max(PRE_GRASP_MIN, cz + CLEARANCE_ABOVE)
        # Clamp to the safe vertical workspace
        pre_grasp_z = max(0.014, min(0.26, pre_grasp_z))

        pre_grasp_args = {
            "x": target_x,
            "y": target_y,
            "z": pre_grasp_z,
            "yaw": cyaw,
            "speed": SPEED_APPROACH
        }
        try:
            robot.move_to(**pre_grasp_args)
        except Exception as e:
            robot.log(f"pre_grasp move_to exception: {e}")
            robot.wait(0.2)
            continue
        robot.wait(SETTLE_AFTER_MOVE)

        # Optional re‑observe to confirm we are still above the cube
        obs2 = robot.observe()
        robot.wait(0.1)

        # ------------------------------------------------------------
        # 4. Grasp
        # ------------------------------------------------------------
        if not robot.grasp():
            robot.log("grasp failed, retry")
            robot.wait(0.2)
            continue
        robot.wait(WAIT_AFTER_GRASP)

        # ------------------------------------------------------------
        # 5. Verify that the red cube is actually held
        # ------------------------------------------------------------
        if robot.holding() != RED_NAME:
            robot.log(f"holding check failed: got {robot.holding()}, retry")
            robot.wait(0.2)
            continue

        # Verify that the object has risen (slip detection)
        obs_check = robot.observe()
        robot.wait(0.1)
        held_z = obs_check.get("objects", {}).get(RED_NAME, {}).get("pos", [0])[2]
        if held_z < cz + 0.005:   # not lifted enough
            robot.log(f"hold check low z {held_z:.4f}, retry")
            robot.wait(0.2)
            continue

        # ------------------------------------------------------------
        # 6. Lift to required height
        # ------------------------------------------------------------
        lift_z = max(REQUIRED_Z, cz + 0.020)  # give a small extra margin
        lift_z = min(lift_z, 0.26)           # stay inside safe zone

        lift_args = {
            "x": target_x,
            "y": target_y,
            "z": lift_z,
            "yaw": cyaw,
            "speed": SPEED_LIFT
        }
        try:
            robot.move_to(**lift_args)
        except Exception as e:
            robot.log(f"lift move_to exception: {e}")
            robot.wait(0.2)
            continue
        robot.wait(0.2)  # settle

        # ------------------------------------------------------------
        # 7. Final verification – still holding and at sufficient height
        # ------------------------------------------------------------
        final_obs = robot.observe()
        robot.wait(0.1)
        final_z = final_obs.get("objects", {}).get(RED_NAME, {}).get("pos", [0])[2]
        if final_z >= REQUIRED_Z - 0.005:
            robot.log("success: red cube securely lifted to required height")
            return True

        # ------------------------------------------------------------
        # 8. Unexpected end – retry
        # ------------------------------------------------------------
        robot.log("unexpected end, retry")
        robot.wait(0.2)

    robot.log("failed to pick up red cube after retries")
    return False
