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
    red = obs['objects'].get('red_cube')
    if red is None:
        # Try to query the pose directly; if it raises LookupError we must
        # move the gripper out of the way and observe again later.
        try:
            pose = robot.get_pose('red_cube')
            red = {'pos': pose['pos'], 'yaw': pose['yaw']}
        except Exception:  # LookupError or any other unexpected error
            robot.log("red_cube not visible; will retry later")
            return False

    # ------------------------------------------------------------------
    # 2. Compute useful poses
    # ------------------------------------------------------------------
    obj_pose = _pose_from_observation(red['pos'], red['yaw'])
    # Desired centre height for grasping (just above the table, near the cube centre)
    grasp_z = 0.015  # roughly the cube centre height
    # Lift height: at least 5 cm above the table (table is at z=0)
    target_z = 0.05
    # A safe pre‑grasp pose: 0.02 m above the cube centre, with a small offset
    # to avoid the gripper colliding with the table.
    offset = 0.02
    pre_grasp = Pose(
        x=obj_pose.x,
        y=obj_pose.y,
        z=obj_pose.z + offset,
        yaw=obj_pose.yaw  # align fingers with cube faces
    )
    # Target pose for holding the cube at the required height
    hold_pose = Pose(
        x=obj_pose.x,
        y=obj_pose.y,
        z=target_z,
        yaw=obj_pose.yaw
    )

    # ------------------------------------------------------------------
    # 3. Move to pre‑grasp pose (above the cube)
    # ------------------------------------------------------------------
    def _try_move_to(p, speed=0.07):
        """Attempt a move_to; return True on success, False on MotionError."""
        try:
            result = robot.move_to(p.x, p.y, p.z, yaw=p.yaw, speed=speed)
            if not result['ok']:
                raise MotionError("move_to blocked")
            return True
        except Exception:  # MotionError or any other exception
            return False

    max_attempts = 3
    for attempt in range(max_attempts):
        if _try_move_to(pre_grasp):
            break
        else:
            # Small random jitter to escape local collision
            jitter = np.random.uniform(-0.01, 0.01, size=3)
            retry_pose = Pose(
                x=pre_grasp.x + jitter[0],
                y=pre_grasp.y + jitter[1],
                z=pre_grasp.z + jitter[2],
                yaw=pre_grasp.yaw
            )
            if attempt == max_attempts - 1:
                robot.log("Failed to reach pre‑grasp pose after retries")
                return False
    else:
        # Should never reach here because of the break on success
        return False

    # ------------------------------------------------------------------
    # 4. Lower to grasp height and close fingers
    # ------------------------------------------------------------------
    # Move down to the cube centre (grasp height)
    grasp_pose = Pose(
        x=pre_grasp.x,
        y=pre_grasp.y,
        z=grasp_z,
        yaw=pre_grasp.yaw
    )
    if not _try_move_to(grasp_pose):
        robot.log("Failed to descend to grasp height")
        return False

    # Close the gripper
    if not robot.grasp():
        robot.log("Grasp command returned False; retrying once")
        # Simple recovery: lift a bit, move a tiny offset, try again
        robot.move_by(dz=0.01, speed=None)
        if not robot.grasp():
            robot.log("Second grasp attempt also failed")
            return False

    # Verify that we are actually holding the cube
    if robot.holding() != 'red_cube':
        robot.log("Object not held after grasp")
        return False

    # ------------------------------------------------------------------
    # 5. Lift to the required height (≥ 5 cm above table)
    # ------------------------------------------------------------------
    if not _try_move_to(hold_pose, speed=0.07):
        robot.log("Failed to lift to target height")
        return False

    # ------------------------------------------------------------------
    # 6. Success
    # ------------------------------------------------------------------
    robot.log("Red cube successfully lifted and held at required height")
    return True
