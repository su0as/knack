# skill module
import math
import numpy as np
from collections import defaultdict

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
        # One of the cubes is hidden – try to move the gripper out of the way
        robot.log("Missing cube in perception, aborting this episode.")
        return False

    # ------------------------------------------------------------------
    # 2. Compute pick and place poses
    # ------------------------------------------------------------------
    # Cube size is 0.03 m → half height = 0.015 m
    half_h = 0.015

    # Pick pose: directly over the red cube centre, same orientation
    pick_x, pick_y, pick_z = red_pose["pos"]
    pick_yaw = red_pose["yaw"]

    # Place pose: centre of the blue cube + height to sit on top of it
    blue_x, blue_y, blue_z = blue_pose["pos"]
    place_z = blue_z + half_h + half_h          # blue top + red half‑height
    place_x, place_y = blue_x, blue_y
    place_yaw = blue_pose["yaw"]               # align fingers with the base cube

    # ------------------------------------------------------------------
    # 3. Move to pick position and grasp
    # ------------------------------------------------------------------
    try:
        robot.log(f"Moving to pick pose: ({pick_x:.3f}, {pick_y:.3f}, {pick_z:.3f}, yaw={pick_yaw:.3f})")
        robot.move_to(pick_x, pick_y, pick_z, yaw=pick_yaw, speed=0.07)
    except MotionError:
        robot.log("Pick pose unreachable – aborting.")
        return False

    robot.log("Closing gripper")
    robot.grasp()

    # Verify that the red cube is actually held
    max_retries = 3
    for attempt in range(max_retries):
        if robot.holding() == "red_cube":
            break
        robot.log(f"Grasp verification failed (attempt {attempt+1}/{max_retries})")
        # Open and try again
        robot.release()
        robot.move_to(pick_x, pick_y, pick_z, yaw=pick_yaw, speed=0.07)
        robot.grasp()
        robot.wait(0.5)  # give the simulation a moment to settle

    else:
        robot.log("Failed to hold red cube after several attempts.")
        return False

    # ------------------------------------------------------------------
    # 4. Move to place position and release
    # ------------------------------------------------------------------
    try:
        robot.log(f"Moving to place pose: ({place_x:.3f}, {place_y:.3f}, {place_z:.3f}, yaw={place_yaw:.3f})")
        robot.move_to(place_x, place_y, place_z, yaw=place_yaw, speed=0.07)
    except MotionError:
        robot.log("Place pose unreachable – aborting.")
        robot.release()
        return False

    robot.log("Opening gripper to release")
    robot.release()

    # Verify release
    if robot.holding() is None:
        robot.log("Release successful.")
        return True
    else:
        robot.log("Release verification failed – attempting recovery.")
        # Simple recovery: move a little up, try again
        robot.move_by(dz=0.02, speed=0.07)
        robot.release()
        robot.wait(0.3)
        return robot.holding() is None
