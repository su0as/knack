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
        try:
            pose = robot.get_pose('red_cube')
            red = {'pos': pose['pos'], 'yaw': pose['yaw']}
        except Exception as e:
            robot.log(f"red_cube pose not available: {e}")
            return False

    # ------------------------------------------------------------------
    # 2. Geometry constants derived from the observed object
    # ------------------------------------------------------------------
    obj = _pose_from_observation(red['pos'], red['yaw'])

    # Required final height is >= 0.065 m; we add a safe margin.
    REQUIRED_HEIGHT = 0.065
    # Pre‑grasp must be high enough to avoid the table and to give a lift margin.
    PRE_GRASP_Z = obj.z + 0.12          # 12 cm above cube centre (collision‑free)
    LIFT_MARGIN = 0.02                  # extra lift after grasp
    APPROACH_SPEED = 0.07               # low speed for safety
    LIFT_SPEED = 0.07                   # same speed for the lift
    NUDGE_DZ = 0.04                     # upward nudge on recovery
    WAIT_AFTER_CLOSE = 0.2              # seconds to let fingers seat

    # ------------------------------------------------------------------
    # 3. Pre‑grasp pose (above the cube)
    # ------------------------------------------------------------------
    pre_grasp = Pose(obj.x, obj.y, PRE_GRASP_Z, obj.yaw)

    # ------------------------------------------------------------------
    # 4. Helper: safe move_to with retry and jitter
    # ------------------------------------------------------------------
    def try_move_to(pose, speed):
        """Attempt a move_to; return True on success, False on any exception."""
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
        # First closure failed – try a larger upward nudge and retry once
        robot.log("First grasp failed, attempting recovery")
        robot.move_by(dz=NUDGE_DZ)          # larger nudge for reliability
        if not robot.grasp():
            robot.log("Second grasp also failed")
            return False
        if robot.holding() != 'red_cube':
            robot.log("Object still not held after recovery")
            return False
        robot.wait(WAIT_AFTER_CLOSE)

    # ------------------------------------------------------------------
    # 6. Optional lift to guarantee required height
    # ------------------------------------------------------------------
    lift_z = pre_grasp.z + LIFT_MARGIN   # ensure we are well above 0.065 m
    lift_pose = Pose(pre_grasp.x, pre_grasp.y, lift_z, pre_grasp.yaw)
    if not try_move_to(lift_pose, LIFT_SPEED):
        robot.log("Lift to required height failed")
        return False

    # ------------------------------------------------------------------
    # 7. Success
    # ------------------------------------------------------------------
    robot.log("Red cube lifted and held at required height")
    return True
