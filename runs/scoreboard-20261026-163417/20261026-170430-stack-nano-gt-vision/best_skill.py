# skill module
import math

# Custom exception from the simulator – we can catch it to avoid halting the skill
class MotionError(Exception):
    pass


def run(robot):
    """
    Stack the red cube on top of the blue cube and release it.
    The function returns True when the stacking is believed to be successful.
    """

    # ------------------------------------------------------------------
    # 1. Perceive the scene
    # ------------------------------------------------------------------
    obs = robot.observe()
    try:
        red_pose = robot.get_pose('red_cube')
        blue_pose = robot.get_pose('blue_cube')
    except LookupError:
        # One of the cubes is hidden – abort this episode.
        robot.log("Missing cube in perception, aborting this episode.")
        return False

    # ------------------------------------------------------------------
    # 2. Compute pick and place poses
    # ------------------------------------------------------------------
    # Cube dimensions (given in the problem statement)
    cube_side = 0.03          # 3 cm per side
    half_h = cube_side / 2    # 0.015 m – half height (and half width)

    # Pick pose: directly over the red cube centre, same orientation
    pick_x, pick_y, pick_z = red_pose["pos"]
    pick_yaw = red_pose["yaw"]

    # Place pose: centre of the blue cube + height to sit on top of it,
    # plus a small safety margin so the cube can settle.
    blue_x, blue_y, blue_z = blue_pose["pos"]
    place_yaw = blue_pose["yaw"]

    # Use a small constant offset (≤ 0.005 m) to counteract XY mis‑alignment.
    OFFSET_MAX = 0.005
    offset_x = OFFSET_MAX * math.cos(place_yaw)
    offset_y = OFFSET_MAX * math.sin(place_yaw)
    place_x = blue_x + offset_x
    place_y = blue_y + offset_y

    # Height: blue top + red half‑height + safety margin (≈0.03 m extra)
    base_place_z = blue_z + half_h + half_h + 0.03   # ≈ blue_z + 0.06 m
    # Clamp to stay inside the robot’s Z workspace (max ≈0.26 m)
    place_z = min(base_place_z, 0.25)

    # ------------------------------------------------------------------
    # 3. Move to pick position, lower slightly, then grasp
    # ------------------------------------------------------------------
    try:
        robot.log(
            f"Moving to pick pose: ({pick_x:.3f}, {pick_y:.3f}, {pick_z:.3f}, yaw={pick_yaw:.3f})"
        )
        # Slightly lower the tool point to ensure finger contact before closing.
        robot.move_to(pick_x, pick_y, pick_z - 0.005, yaw=pick_yaw, speed=0.12)
    except MotionError:
        robot.log("Pick pose unreachable – aborting.")
        return False

    robot.log("Closing gripper")
    robot.grasp()

    # Verify that the red cube is actually held; retry a few times.
    max_retries = 5
    for attempt in range(max_retries):
        if robot.holding() == "red_cube":
            break
        robot.log(f"Grasp verification failed (attempt {attempt+1}/{max_retries})")
        # Open and try again
        robot.release()
        robot.wait(0.2)                     # give simulation a moment to settle
        try:
            robot.move_to(pick_x, pick_y, pick_z - 0.005, yaw=pick_yaw, speed=0.12)
        except MotionError:
            robot.log("Re‑approach to pick pose failed – aborting.")
            return False
        robot.grasp()
        robot.wait(0.5)                     # let the grasp settle

    else:
        robot.log("Failed to hold red cube after several attempts.")
        return False

    # ------------------------------------------------------------------
    # 4. Move to place position, wait, then release
    # ------------------------------------------------------------------
    try:
        robot.log(
            f"Moving to place pose: ({place_x:.3f}, {place_y:.3f}, {place_z:.3f}, yaw={place_yaw:.3f})"
        )
        robot.move_to(place_x, place_y, place_z, yaw=place_yaw, speed=0.07)
    except MotionError:
        robot.log("Place pose unreachable – aborting.")
        robot.release()
        return False

    # Small pause to ensure we are stable above the target before releasing.
    robot.wait(0.3)

    robot.log("Opening gripper to release")
    robot.release()
    robot.wait(0.2)   # let the release settle

    # Verify release
    if robot.holding() is None:
        robot.log("Release successful.")
        return True
    else:
        robot.log("Release verification failed – attempting recovery.")
        # Simple recovery: lift a little, try releasing again.
        try:
            robot.move_by(dz=0.02, speed=0.07)
            robot.release()
            robot.wait(0.3)
        except MotionError:
            robot.log("Recovery move failed.")
        return robot.holding() is None
