import math

def run(robot):
    # Start from a known safe pose
    robot.home()

    # Get the current scene
    obs = robot.observe()

    # Identify all cubes in the scene
    cubes = [name for name, info in obs['objects'].items() if info.get('shape') == 'cube']

    # Safety heights
    SAFE_Z = 0.08          # high enough to clear obstacles
    GRASP_OFFSET = 0.005   # a little above the cube centre for grasping
    PLACE_OFFSET = 0.005   # a little above the tray bottom for placing

    for cube_name in cubes:
        cube_info = obs['objects'][cube_name]
        colour = cube_info['color']

        # Find the tray that matches the cube's colour
        tray_name = None
        for name, fix in obs['fixtures'].items():
            if fix.get('kind') == 'tray' and fix.get('color') == colour:
                tray_name = name
                break
        if tray_name is None:
            # No matching tray – skip this cube
            continue

        try:
            cube_pose = robot.get_pose(cube_name)
            tray_pose = robot.get_pose(tray_name)
        except LookupError:
            # If we cannot get a pose (occluded), move the gripper aside and try to re‑observe
            robot.move_by(dz=0.05)  # lift a bit
            robot.wait(0.2)
            obs = robot.observe()
            try:
                cube_pose = robot.get_pose(cube_name)
                tray_pose = robot.get_pose(tray_name)
            except LookupError:
                # Still missing – give up on this object
                robot.log(f"Could not locate {cube_name} or {tray_name}")
                continue

        # ----- Pick the cube -----
        # 1. Move to a safe position above the cube
        above_cube = [cube_pose['pos'][0], cube_pose['pos'][1], SAFE_Z]
        res = robot.move_to(*above_cube, yaw=cube_pose['yaw'])
        if not res['ok']:
            robot.log(f"Failed to move above {cube_name}")
            continue

        # 2. Descend to grasping height
        grasp_pos = [cube_pose['pos'][0], cube_pose['pos'][1],
                     cube_pose['pos'][2] + GRASP_OFFSET]
        res = robot.move_to(*grasp_pos, yaw=cube_pose['yaw'], speed=0.05)
        if not res['ok']:
            robot.log(f"Failed to descend to grasp {cube_name}")
            continue

        # 3. Close the fingers
        if not robot.grasp():
            robot.log(f"Grasp failed on {cube_name}")
            # Retreat and try next object
            robot.move_to(*above_cube, yaw=cube_pose['yaw'])
            continue

        # 4. Lift the cube to a safe height
        robot.move_to(*above_cube, yaw=cube_pose['yaw'])

        # ----- Place the cube in the matching tray -----
        # 1. Move above the tray
        above_tray = [tray_pose['pos'][0], tray_pose['pos'][1], SAFE_Z]
        robot.move_to(*above_tray, yaw=tray_pose['yaw'])

        # 2. Lower to just above the tray bottom
        place_pos = [tray_pose['pos'][0], tray_pose['pos'][1],
                     tray_pose['pos'][2] + PLACE_OFFSET]
        robot.move_to(*place_pos, yaw=tray_pose['yaw'], speed=0.05)

        # 3. Release the cube
        robot.release()

        # 4. Lift again
        robot.move_to(*above_tray, yaw=tray_pose['yaw'])

    # Indicate that the skill finished (success is judged externally)
    return True
