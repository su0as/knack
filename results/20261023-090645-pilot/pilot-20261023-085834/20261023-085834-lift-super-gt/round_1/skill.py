import math

def run(robot):
    """
    Pick up the red cube and hold it at least 5 cm above the table.
    Returns True if the task appears to have succeeded, otherwise False.
    """
    # Start from a known safe pose
    robot.home()

    # ------------------------------------------------------------------
    # 1. Locate the red cube
    # ------------------------------------------------------------------
    obs = robot.observe()
    red_info = obs.get('objects', {}).get('red_cube')
    if red_info:
        cube_pos = red_info['pos']
        cube_yaw = red_info['yaw']
    else:
        # Fallback to direct query (should rarely be needed)
        pose = robot.get_pose('red_cube')
        cube_pos = pose['pos']
        cube_yaw = pose['yaw']

    # Cube dimensions (all cubes are 0.03 m per side)
    half_size = 0.03 / 2.0          # 0.015 m
    grasp_z = cube_pos[2]           # tool point at cube centre → fingers around mid‑height
    lift_z = cube_pos[2] + 0.05     # 5 cm above the table top (cube centre + 0.05)

    # Helper to attempt a pick‑and‑lift sequence
    def attempt():
        try:
            # Move to a safe clearance above the cube
            robot.move_to(cube_pos[0], cube_pos[1], cube_pos[2] + 0.10,
                          yaw=cube_yaw, speed=0.15)
            # Descend slowly to the grasp height
            robot.move_to(cube_pos[0], cube_pos[1], grasp_z,
                          yaw=cube_yaw, speed=0.05)
            # Close the fingers
            if not robot.grasp():
                return False
            # Lift to the target height
            robot.move_to(cube_pos[0], cube_pos[1], lift_z,
                          yaw=cube_yaw, speed=0.15)
            # Verify that we are holding the red cube and are high enough
            if robot.holding() != 'red_cube':
                return False
            grip_pose = robot.observe()['gripper']['pos']
            # Allow a small tolerance (2 mm) for noise and control error
            return grip_pose[2] >= lift_z - 0.002
        except MotionError as e:
            robot.log("MotionError during attempt:", e)
            return False

    # ------------------------------------------------------------------
    # 2. First attempt
    # ------------------------------------------------------------------
    if attempt():
        robot.log("Pick‑up succeeded on first try.")
        return True

    # ------------------------------------------------------------------
    # 3. Recovery: open fingers, home, then try once more
    # ------------------------------------------------------------------
    robot.release()
    robot.home()
    robot.log("First attempt failed; retrying...")

    if attempt():
        robot.log("Pick‑up succeeded on second try.")
        return True

    # ------------------------------------------------------------------
    # 4. Final cleanup
    # ------------------------------------------------------------------
    robot.release()
    robot.home()
    robot.log("Pick‑up failed after two attempts.")
    return False
