# skill module
import math
import itertools

def run(robot):
    """
    Pick up the red cube and hold it at least 5 cm above the table.
    Returns True when the cube is securely held at the target height.
    """
    RED_NAME = "red_cube"
    # Required clearance above the table (metres)
    REQUIRED_Z = 0.065          # 5 cm above the tabletop
    # Height for the low‑z pre‑grasp pose (just above the cube base)
    PRE_GRASP_Z = 0.055
    # Extra safety margin added to the final lift height
    # LIFT_Z is now computed per‑episode: REQUIRED_Z + observed base height
    # Speeds
    SPEED_APPROACH = 0.10       # short pre‑grasp move (still safe)
    SPEED_LIFT = 0.07           # slower lift to stay within safety layer
    # Horizontal safety offset to stay inside the reachable band
    HOFFSET = 0.005
    # Wait times (seconds)
    WAIT_AFTER_OBSERVE = 0.5
    WAIT_AFTER_MOVE = 0.1
    SETTLE_AFTER_MOVE = 0.05   # extra settle before closing
    WAIT_AFTER_GRASP = 0.2
    MAX_RETRIES = 12

    for attempt in range(MAX_RETRIES):
        # 1. Perceive the scene and wait for a stable observation
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

        # 2. Compute a safe tool‑point just above the cube centre
        # Apply a small signed offset but clamp to the reachable workspace
        offset_x = HOFFSET if cx >= 0 else -HOFFSET
        offset_y = HOFFSET if cy >= 0 else -HOFFSET
        target_x = cx + offset_x
        target_y = cy + offset_y
        # Clamp to the robot's reachable area
        target_x = max(0.04, min(0.32, target_x))
        target_y = max(-0.26, min(0.26, target_y))

        # 3. Pre‑grasp move (low z, faster speed)
        pre_grasp_args = {
            "x": target_x,
            "y": target_y,
            "z": PRE_GRASP_Z,
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

        # 4. Attempt to close the gripper
        if not robot.grasp():
            robot.log("grasp failed, retry")
            robot.wait(0.2)
            continue
        robot.wait(WAIT_AFTER_GRASP)

        # 5. Verify that the red cube is actually held
        if robot.holding() != RED_NAME:
            robot.log(f"holding check failed: got {robot.holding()}, retry")
            robot.wait(0.2)
            continue

        # 6. Lift to the required height (clearance + observed base height)
        lift_z = REQUIRED_Z + cz  # e.g. 0.065 + ~0.015 = 0.080 m
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
        robot.wait(0.2)  # let the lift settle

        # 7. Final verification – still holding and at sufficient height
        if robot.holding() == RED_NAME:
            # Double‑check the cube's reported z is at least REQUIRED_Z (allow tiny noise)
            final_obs = robot.observe()
            robot.wait(0.1)
            final_z = final_obs.get("objects", {}).get(RED_NAME, {}).get("pos", [0])[2]
            if final_z >= REQUIRED_Z - 0.005:
                robot.log("success: red cube securely lifted to required height")
                return True

        # 8. Unexpected end – retry
        robot.log("unexpected end, retry")
        robot.wait(0.2)

    # Failure after all retries
    robot.log("failed to pick up red cube after retries")
    return False
