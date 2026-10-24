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
    # Pre‑grasp height: start a little above the observed centre,
    # but allow a lower floor for very flat objects.
    # Safety margin: at least 0.016 m and at least 1 mm above the centre.
    PRE_GRASP_MIN = 0.016
    HEIGHT_OFFSET = 0.001        # 1 mm above centre
    # Speeds
    SPEED_APPROACH = 0.10
    SPEED_LIFT = 0.07
    # Horizontal offset to stay away from object edges
    HOFFSET = 0.005
    # Wait times
    WAIT_AFTER_OBSERVE = 0.5
    WAIT_AFTER_MOVE = 0.1
    SETTLE_AFTER_MOVE = 0.05
    WAIT_AFTER_GRASP = 0.2
    MAX_RETRIES = 12

    for attempt in range(MAX_RETRIES):
        # ------------------------------------------------------------
        # 1. Perceive
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
        # 2. Target position (horizontal offset, clamped)
        # ------------------------------------------------------------
        offset_x = HOFFSET if cx >= 0 else -HOFFSET
        offset_y = HOFFSET if cy >= 0 else -HOFFSET
        target_x = cx + offset_x
        target_y = cy + offset_y
        target_x = max(0.04, min(0.32, target_x))
        target_y = max(-0.26, min(0.26, target_y))

        # ------------------------------------------------------------
        # 3. Pre‑grasp pose (just above the cube)
        # ------------------------------------------------------------
        # Lower floor to 0.008 m, then enforce safety margin.
        pre_grasp_z_raw = max(0.008, cz - 0.002)          # lower floor
        pre_grasp_z = max(PRE_GRASP_MIN, pre_grasp_z_raw, cz + HEIGHT_OFFSET)
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

        # ------------------------------------------------------------
        # 4. Grasp
        # ------------------------------------------------------------
        if not robot.grasp():
            robot.log("grasp failed, retry")
            robot.wait(0.2)
            continue
        robot.wait(WAIT_AFTER_GRASP)

        # ------------------------------------------------------------
        # 5. Verify hold
        # ------------------------------------------------------------
        if robot.holding() != RED_NAME:
            robot.log(f"holding check failed: got {robot.holding()}, retry")
            robot.wait(0.2)
            continue

        # ------------------------------------------------------------
        # 6. Lift to required height (guaranteed clearance)
        # ------------------------------------------------------------
        # Desired lift height: required clearance plus a bit above the cube centre.
        lift_z_raw = REQUIRED_Z + cz          # typical ~0.080 m
        lift_z = max(REQUIRED_Z, lift_z_raw)  # ensure minimum clearance
        lift_z = min(lift_z, 0.26)            # stay inside workspace ceiling

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
        if robot.holding() == RED_NAME:
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
