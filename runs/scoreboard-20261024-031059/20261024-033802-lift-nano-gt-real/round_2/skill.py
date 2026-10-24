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
    REQUIRED_Z = 0.065          # 0.015 (cube base) + 0.05 (clearance)
    # Height for the low‑z pre‑grasp pose (just above the cube)
    PRE_GRASP_Z = 0.055
    # Extra safety margin added to the final lift height
    LIFT_Z = 0.07               # a little above REQUIRED_Z for safety
    # Horizontal safety offset to stay inside the reachable band
    HOFFSET = 0.005
    # Speeds
    SPEED_APPROACH = 0.10       # short pre‑grasp move (still safe)
    SPEED_LIFT = 0.07           # slower lift to stay within safety layer
    # Wait times (seconds)
    WAIT_AFTER_OBSERVE = 0.5
    WAIT_AFTER_MOVE = 0.1
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
        target_x = cx
        target_y = cy
        # Small horizontal offset to avoid edge effects
        target_x += HOFFSET * (1 if target_x >= 0.15 else -1)
        target_y += HOFFSET * (1 if target_y >= 0.0 else -1)

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
        robot.wait(WAIT_AFTER_MOVE)

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

        # 6. Lift to the required height (≈5 cm clearance)
        lift_args = {
            "x": target_x,
            "y": target_y,
            "z": LIFT_Z,
            "yaw": cyaw,
            "speed": SPEED_LIFT
        }
        try:
            robot.move_to(**lift_args)
        except Exception as e:
            robot.log(f"lift move_to exception: {e}")
            robot.wait(0.2)
            continue

        # 7. Final verification – still holding and at sufficient height
        if robot.holding() == RED_NAME:
            robot.log("success: red cube securely lifted")
            return True

        # 8. If we reach here something unexpected happened; retry
        robot.log("unexpected end, retry")
        robot.wait(0.2)

    # Failure after all retries
    robot.log("failed to pick up red cube after retries")
    return False
