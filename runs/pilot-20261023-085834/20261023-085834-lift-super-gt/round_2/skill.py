import math

def run(robot):
    """
    Pick up the red cube and hold it at least 5 cm above the table.
    Returns True if the task appears to have succeeded, otherwise False.
    """
    # Start from a known safe pose
    robot.home()

    def attempt():
        """Try to pick up the red cube once."""
        # Fresh perception for this attempt
        obs = robot.observe()
        red_info = obs.get('objects', {}).get('red_cube')
        if not red_info:
            # Fallback to direct query (should rarely be needed)
            pose = robot.get_pose('red_cube')
            red_info = {'pos': pose['pos'], 'yaw': pose['yaw']}
        cube_pos = red_info['pos']
        cube_yaw = red_info['yaw']

        # Desired heights
        grasp_z = cube_pos[2]                     # tool point at cube centre
        lift_z = max(cube_pos[2] + 0.05, 0.065)   # at least 5 cm above table

        try:
            # 1. Move to a safe clearance above the cube
            robot.move_to(cube_pos[0], cube_pos[1], cube_pos[2] + 0.10,
                          yaw=cube_yaw, speed=0.15)

            # 2. Pre‑grasp approach: move slowly to 2 cm above the cube
            robot.move_to(cube_pos[0], cube_pos[1], cube_pos[2] + 0.02,
                          yaw=cube_yaw, speed=0.05)

            # 3. Descend slowly to the grasp height (final centimetres)
            robot.move_to(cube_pos[0], cube_pos[1], grasp_z,
                          yaw=cube_yaw, speed=0.02)

            # 4. Close the fingers
            if not robot.grasp():
                return False

            # 5. Lift to the target height
            robot.move_to(cube_pos[0], cube_pos[1], lift_z,
                          yaw=cube_yaw, speed=0.15)

            # 6. Verify grasp and height
            if robot.holding() != 'red_cube':
                return False
            grip_pose = robot.observe()['gripper']['pos']
            # Allow 2 mm tolerance for noise and control error
            return grip_pose[2] >= lift_z - 0.002

        except Exception as e:
            robot.log("MotionError during attempt:", e)
            return False

    # ------------------------------------------------------------------
    # First attempt
    # ------------------------------------------------------------------
    if attempt():
        robot.log("Pick‑up succeeded on first try.")
        return True

    # ------------------------------------------------------------------
    # Recovery: open fingers, home, then try once more
    # ------------------------------------------------------------------
    robot.release()
    robot.home()
    robot.log("First attempt failed; retrying...")

    if attempt():
        robot.log("Pick‑up succeeded on second try.")
        return True

    # ------------------------------------------------------------------
    # Final cleanup
    # ------------------------------------------------------------------
    robot.release()
    robot.home()
    robot.log("Pick‑up failed after two attempts.")
    return False
