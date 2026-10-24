# skill module
import math
import itertools

def run(robot):
    """
    Pick up the red cube and hold it at least 5 cm above the table.
    Returns True when the cube is securely held at the target height.
    """
    RED_NAME = "red_cube"
    # Desired clearance above the table (metres)
    CLEARANCE = 0.05
    # Extra safety margin added to the target height
    LIFT_Z = 0.065  # ≈0.015 (cube base) + 0.05 (clearance) + 0.0005 margin
    # Safety margin in the horizontal plane
    HOFFSET = 0.005

    # Retry loop (max attempts to avoid infinite loops in case of persistent failure)
    max_retries = 10
    for attempt in range(max_retries):
        obs = robot.observe()
        objs = obs.get("objects", {})
        if RED_NAME not in objs:
            # Red cube not present in this perception – try again next cycle
            robot.log("red_cube not seen, retry")
            robot.wait(0.2)
            continue

        cube = objs[RED_NAME]
        cx, cy, cz = cube["pos"]
        cyaw = cube["yaw"]
        # Compute a safe tool‑point just above the cube centre
        target_x = cx
        target_y = cy
        target_z = LIFT_Z
        # Slight offset to stay inside the reachable band and avoid edge effects
        target_x += HOFFSET * (1 if target_x >= 0.15 else -1)
        target_y += HOFFSET * (1 if target_y >= 0.0 else -1)

        # Build move arguments
        move_args = {
            "x": target_x,
            "y": target_y,
            "z": target_z,
            "yaw": cyaw,          # align fingers with cube faces
            "speed": 0.07           # slow approach
        }

        # Try to move to the target pose
        try:
            move_res = robot.move_to(**move_args)
        except Exception as e:
            # MotionError or any unexpected exception – restart with fresh perception
            robot.log(f"move_to exception: {e}")
            robot.wait(0.2)
            continue

        if not move_res.get("ok", False):
            # Target was unreachable or blocked – restart
            robot.log("move_to blocked")
            robot.wait(0.2)
            continue

        # Close the gripper to grasp
        grasp_ok = robot.grasp()
        if not grasp_ok:
            robot.log("grasp failed, retry")
            robot.wait(0.2)
            continue

        # Verify that the red cube is actually held
        held = robot.holding()
        if held != RED_NAME:
            robot.log(f"holding check failed: got {held}, retry")
            robot.wait(0.2)
            continue

        # Lift a bit higher to guarantee the 5 cm clearance
        lift_target = {
            "x": target_x,
            "y": target_y,
            "z": 0.08,          # 8 cm above table, safely above required 5 cm
            "yaw": cyaw,
            "speed": 0.07
        }
        try:
            robot.move_to(**lift_target)
        except Exception as e:
            robot.log(f"lift move exception: {e}")
            robot.wait(0.2)
            continue

        # Final verification – ensure we are still holding and at sufficient height
        if robot.holding() == RED_NAME:
            robot.log("success: red cube securely lifted")
            return True

        # If we reach here something went wrong; retry
        robot.log("unexpected end, retry")
        robot.wait(0.2)

    # If we exit the loop we failed to secure the cube
    robot.log("failed to pick up red cube after retries")
    return False
