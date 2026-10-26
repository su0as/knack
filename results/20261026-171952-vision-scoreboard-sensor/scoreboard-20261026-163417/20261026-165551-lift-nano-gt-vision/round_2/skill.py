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
        # Try to query the pose directly; if it raises MotionError we must
        # give up for this episode.
        try:
            pose = robot.get_pose('red_cube')
            red = {'pos': pose['pos'], 'yaw': pose['yaw']}
        except MotionError:
            robot.log("red_cube pose not available yet")
            return False
        except Exception as e:  # any other unexpected error
            robot.log(f"Error getting red_cube pose: {e}")
            return False

    # ------------------------------------------------------------------
    # 2. Compute useful poses and constants
    # ------------------------------------------------------------------
    obj = _pose_from_observation(red['pos'], red['yaw'])

    # Cube centre is roughly at z = 0.015 m.
    # We need a final pose with z >= 0.05 m; add a safety margin.
    GRASP_Z = 0.015          # height just above the table, near cube centre
    TARGET_Z = 0.055         # 5.5 cm, safe margin over the 5 cm requirement
    OFFSET = 0.04            # pre‑grasp offset to reach ~0.055 m
    PRE_GRASP_Z = obj.z + OFFSET

    # Speeds (low to stay within safety limits)
    APPROACH_SPEED = 0.07
    LIFT_SPEED = 0.07

    # ------------------------------------------------------------------
    # 3. Pre‑grasp pose (above the cube)
    # ------------------------------------------------------------------
    pre_grasp = Pose(obj.x, obj.y, PRE_GRASP_Z, obj.yaw)

    # ------------------------------------------------------------------
    # 4. Move to pre‑grasp (with retries)
    # ------------------------------------------------------------------
    def try_move_to(pose, speed):
        """Attempt a move_to; return True on success, False on MotionError."""
        try:
            result = robot.move_to(pose.x, pose.y, pose.z,
                                   yaw=pose.yaw, speed=speed)
            if not result['ok']:
                raise MotionError("move_to blocked")
            return True
        except MotionError:
            return False

    # Up to three attempts with a small jitter if the first try fails
    for _ in range(3):
        if try_move_to(pre_grasp, APPROACH_SPEED):
            break
        jitter = np.random.uniform(-0.01, 0.01, size=3)
        retry_pose = Pose(
            pre_grasp.x + jitter[0],
            pre_grasp.y + jitter[1],
            pre_grasp.z + jitter[2],
            pre_grasp.yaw
        )
        if not try_move_to(retry_pose, APPROACH_SPEED):
            robot.log("Failed to reach pre‑grasp after retries")
            return False

    # ------------------------------------------------------------------
    # 5. Descend to grasp height
    # ------------------------------------------------------------------
    grasp_z_pose = Pose(pre_grasp.x, pre_grasp.y, GRASP_Z, pre_grasp.yaw)
    if not try_move_to(grasp_z_pose, APPROACH_SPEED):
        robot.log("Failed to descend to grasp height")
        return False

    # ------------------------------------------------------------------
    # 6. Close the gripper
    # ------------------------------------------------------------------
    if not robot.grasp():
        robot.log("First grasp failed, retrying once")
        # Simple recovery: lift a little and try again
        robot.move_by(dz=0.01)  # small upward nudge
        if not robot.grasp():
            robot.log("Second grasp also failed")
            return False

    # ------------------------------------------------------------------
    # 7. Verify that the cube is actually held
    # ------------------------------------------------------------------
    if robot.holding() != 'red_cube':
        robot.log("Object not held after grasp")
        return False

    # ------------------------------------------------------------------
    # 8. Anti‑slip delay – let the fingers close fully
    # ------------------------------------------------------------------
    robot.wait(0.3)  # 300 ms pause

    # ------------------------------------------------------------------
    # 9. Lift to the required height (≥ 5 cm)
    # ------------------------------------------------------------------
    hold_pose = Pose(pre_grasp.x, pre_grasp.y, TARGET_Z, pre_grasp.yaw)
    if not try_move_to(hold_pose, LIFT_SPEED):
        robot.log("Failed to lift to target height")
        return False

    # ------------------------------------------------------------------
    # 10. Success
    # ------------------------------------------------------------------
    robot.log("Red cube lifted and held at required height")
    return True
