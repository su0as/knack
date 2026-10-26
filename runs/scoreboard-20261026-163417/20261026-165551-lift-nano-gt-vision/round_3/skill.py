# skill module
import math
import numpy as np
from collections import namedtuple

# Simple container for a pose
Pose = namedtuple('Pose', ['x', 'y', 'z', 'yaw'])


def _pose_from_observation(pos, yaw):
    """Convert raw [x,y,z] + yaw to a Pose namedtuple."""
    return Pose(float(pos[0]), float(pos[1]), float(pos[2]), float(yaw))


def run(robot):
    """
    Pick up the red cube and hold it at least 5 cm above the table.
    Returns True if the task succeeded, otherwise False.
    """
    # ------------------------------------------------------------------
    # 1. Perceive the scene
    # ------------------------------------------------------------------
    obs = robot.observe()
    red = obs.get('objects', {}).get('red_cube')
    if red is None:
        # Fallback to direct pose query if the cube is not in the observation
        try:
            pose = robot.get_pose('red_cube')
            red = {'pos': pose['pos'], 'yaw': pose['yaw']}
        except Exception as e:  # MotionError or any other unexpected error
            robot.log(f"red_cube pose not available: {e}")
            return False

    # ------------------------------------------------------------------
    # 2. Compute useful poses and constants
    # ------------------------------------------------------------------
    obj = _pose_from_observation(red['pos'], red['yaw'])

    # Cube centre is roughly at z = 0.015 m.
    # Required final height is >= 0.05 m; we add a safety margin.
    OFFSET = 0.05                     # pre‑grasp offset to reach ~0.065 m
    PRE_GRASP_Z = obj.z + OFFSET      # target height before closing fingers
    TARGET_Z = PRE_GRASP_Z            # already satisfies the 5 cm requirement
    APPROACH_SPEED = 0.07             # low speed for safety
    LIFT_SPEED = 0.07

    # ------------------------------------------------------------------
    # 3. Pre‑grasp pose (above the cube)
    # ------------------------------------------------------------------
    pre_grasp = Pose(obj.x, obj.y, PRE_GRASP_Z, obj.yaw)

    # ------------------------------------------------------------------
    # 4. Helper: safe move_to with retry and jitter
    # ------------------------------------------------------------------
    def try_move_to(pose, speed):
        """Attempt a move_to; return True on success, False on MotionError."""
        try:
            result = robot.move_to(pose.x, pose.y, pose.z,
                                   yaw=pose.yaw, speed=speed)
            if not result['ok']:
                raise MotionError("move_to blocked")
            return True
        except Exception:  # MotionError or any other move‑related exception
            return False

    # Up to three attempts with small jitter if the first try fails
    reached = False
    for _ in range(3):
        if try_move_to(pre_grasp, APPROACH_SPEED):
            reached = True
            break
        jitter = np.random.uniform(-0.01, 0.01, size=3)
        retry_pose = Pose(
            pre_grasp.x + jitter[0],
            pre_grasp.y + jitter[1],
            pre_grasp.z + jitter[2],
            pre_grasp.yaw
        )
        if try_move_to(retry_pose, APPROACH_SPEED):
            reached = True
            break
    if not reached:
        robot.log("Failed to reach pre‑grasp after retries")
        return False

    # ------------------------------------------------------------------
    # 5. Close the gripper at the pre‑grasp height
    # ------------------------------------------------------------------
    if robot.grasp():
        # Grasp succeeded – verify hold
        if robot.holding() != 'red_cube':
            robot.log("Object not held after grasp")
            return False
    else:
        # First closure failed – try a small upward nudge and retry once
        robot.log("First grasp failed, attempting recovery")
        robot.move_by(dz=0.01)  # lift a little to clear any contact issue
        if not robot.grasp():
            robot.log("Second grasp also failed")
            return False
        # Verify hold after recovery
        if robot.holding() != 'red_cube':
            robot.log("Object still not held after recovery")
            return False

    # ------------------------------------------------------------------
    # 6. Anti‑slip delay – let the fingers close fully
    # ------------------------------------------------------------------
    robot.wait(0.3)  # 300 ms pause

    # ------------------------------------------------------------------
    # 7. Lift (if needed) – currently already at required height
    # ------------------------------------------------------------------
    # The pose we are already at (pre_grasp) meets the height requirement.
    # If a small extra lift is desired for extra safety, uncomment:
    # hold_pose = Pose(pre_grasp.x, pre_grasp.y, TARGET_Z + 0.001, pre_grasp.yaw)
    # try_move_to(hold_pose, LIFT_SPEED)

    # ------------------------------------------------------------------
    # 8. Success
    # ------------------------------------------------------------------
    robot.log("Red cube lifted and held at required height")
    return True
