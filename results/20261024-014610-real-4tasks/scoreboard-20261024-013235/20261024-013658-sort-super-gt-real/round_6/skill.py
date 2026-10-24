import math

def run(robot):
    """Sort cubes by colour into matching trays."""
    robot.home()

    # Get current scene description
    obs = robot.observe()

    # Separate cubes and trays
    cubes = {name: obj for name, obj in obs['objects'].items() if obj['shape'] == 'cube'}
    trays = {name: fix for name, fix in obs['fixtures'].items() if fix['kind'] == 'tray'}

    # Build colour -> tray name mapping (with debugging)
    colour_to_tray = {}
    for name, fix in trays.items():
        colour_to_tray[fix['color']] = name
    robot.log(f"Colour->tray mapping: {colour_to_tray}")

    overall_success = True

    for cube_name, cube in cubes.items():
        colour = cube['color']
        # Try exact match first, then fallback to substring match
        tray_name = colour_to_tray.get(colour)
        if tray_name is None:
            # Fallback: look for a tray whose colour string contains the cube colour (case‑insensitive)
            for t_name, fix in trays.items():
                if colour.lower() in fix['color'].lower():
                    tray_name = t_name
                    break
        if tray_name is None:
            robot.log(f"No tray found for colour '{colour}'")
            overall_success = False
            continue

        # Get up-to-date poses (perception is noisy)
        cube_pose = robot.get_pose(cube_name)
        tray_pose = robot.get_pose(tray_name)

        if not _pick_and_place(robot, cube_pose, tray_pose, cube_name, tray_name):
            robot.log(f"Failed to place {cube_name} into {tray_name}")
            overall_success = False

    return overall_success


def _pick_and_place(robot, cube_pose, tray_pose, cube_name, tray_name):
    """Attempt one pick‑and‑place cycle. Returns True on success."""
    max_attempts = 2
    lift_height = 0.10          # safe travel height above the table
    grasp_offset = 0.04         # how far above the cube centre we close the fingers (increased for reliability)
    place_offset = 0.02         # how far above the tray bottom we release
    tolerance = 0.04            # acceptable xy error for placement (metres)

    for attempt in range(max_attempts):
        try:
            # 1. Move above the cube
            above_cube = [cube_pose['pos'][0], cube_pose['pos'][1], lift_height]
            robot.move_to(*above_cube, speed=0.2)

            # 2. Descend to a grasp height (just above the cube centre) with yaw alignment
            grasp_z = cube_pose['pos'][2] + grasp_offset
            robot.move_to(cube_pose['pos'][0], cube_pose['pos'][1], grasp_z,
                          speed=0.05, yaw=cube_pose['yaw'])

            # 3. Close fingers
            if not robot.grasp():
                robot.release()  # ensure hand is open before retrying
                continue

            # 4. Verify we actually hold something
            if robot.holding() is None:
                robot.release()
                continue

            # 5. Lift the cube to safe height
            robot.move_to(cube_pose['pos'][0], cube_pose['pos'][1], lift_height,
                          speed=0.05)

            # 6. Move above the target tray
            above_tray = [tray_pose['pos'][0], tray_pose['pos'][1], lift_height]
            robot.move_to(*above_tray, speed=0.2)

            # 7. Lower to just above the tray bottom with yaw alignment
            place_z = tray_pose['pos'][2] + place_offset
            robot.move_to(tray_pose['pos'][0], tray_pose['pos'][1], place_z,
                          speed=0.05, yaw=tray_pose['yaw'])

            # 8. Release the cube
            robot.release()
            robot.wait(0.05)  # brief pause to let the object settle

            # 9. Retract to safe height
            robot.move_to(tray_pose['pos'][0], tray_pose['pos'][1], lift_height,
                          speed=0.05)

            # 10. Verification: cube should be released and near tray centre
            cube_after = robot.get_pose(cube_name)
            tray_after = robot.get_pose(tray_name)  # tray pose is static but refresh anyway
            dx = cube_after['pos'][0] - tray_after['pos'][0]
            dy = cube_after['pos'][1] - tray_after['pos'][1]
            if math.hypot(dx, dy) > tolerance:
                robot.log(f"Verification failed: cube {cube_name} off target by {math.hypot(dx, dy):.3f} m")
                # Ensure hand is open before retrying
                robot.release()
                continue

            return True  # success for this cube

        except Exception as e:  # catches MotionError and other unexpected issues
            robot.log(f"Attempt {attempt+1} failed: {e}")
            robot.release()  # try to leave the hand open
            continue

    # If we exit the loop, all attempts failed
    return False
