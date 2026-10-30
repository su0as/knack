import math

def run(robot):
    """Pick up the red cube and hold it at least 5 cm above the table."""
    MAX_RETRIES = 3
    GRASP_HEIGHT = 0.015   # approx centre of cube on table (finger pads around middle)
    LIFT_HEIGHT = 0.05     # 5 cm lift

    # Helper: try to get the pose of the red cube, returning None if not visible
    def get_red_pose():
        try:
            return robot.get_pose('red_cube')
        except LookupError:
            return None

    # Start from a known safe pose
    robot.home()

    for attempt in range(MAX_RETRIES):
        # 1. Perceive the cube
        pose = get_red_pose()
        if pose is None:
            # If we can't see it, move the gripper a bit to the side and try again
            robot.move_by(dx=0.05, dy=0.0, dz=0.05, speed=0.1)
            robot.wait(0.2)
            continue

        # 2. Move above the cube
        above_pos = [pose['pos'][0], pose['pos'][1], 0.10]  # 10 cm clearance
        move_res = robot.move_to(above_pos[0], above_pos[1], above_pos[2],
                                 yaw=pose['yaw'], speed=0.15)
        if not move_res['ok']:
            # If blocked, try a small retreat and retry perception
            robot.move_by(dz=-0.02, speed=0.1)
            continue

        # 3. Descend to grasp height
        grasp_pos = [pose['pos'][0], pose['pos'][1], GRASP_HEIGHT]
        move_res = robot.move_to(grasp_pos[0], grasp_pos[1], grasp_pos[2],
                                 yaw=pose['yaw'], speed=0.08)
        if not move_res['ok']:
            # Retry from above
            robot.move_to(above_pos[0], above_pos[1], above_pos[2],
                          yaw=pose['yaw'], speed=0.15)
            continue

        # 4. Attempt to grasp
        robot.grasp()
        robot.wait(0.2)  # let fingers close
        if robot.holding() != 'red_cube':
            # Grasp failed – open fingers, lift a bit and try again
            robot.release()
            robot.move_by(dz=0.03, speed=0.1)
            continue

        # 5. Lift the cube 5 cm above the table
        lift_pos = [pose['pos'][0], pose['pos'][1], GRASP_HEIGHT + LIFT_HEIGHT]
        move_res = robot.move_to(lift_pos[0], lift_pos[1], lift_pos[2],
                                 yaw=pose['yaw'], speed=0.15)
        if not move_res['ok']:
            # Something went wrong while lifting; release and retry
            robot.release()
            robot.home()
            continue

        # 6. Verify we are still holding the cube after the lift
        if robot.holding() == 'red_cube':
            return True
        else:
            # Lost hold – release and retry from scratch
            robot.release()
            robot.home()
            continue

    # If we exhausted retries without success, ensure a safe state
    robot.release()
    robot.home()
    return False
