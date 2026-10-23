import math

def run(robot):
    # Get initial scene snapshot
    obs = robot.observe()
    objects = obs.get("objects", {})
    fixtures = obs.get("fixtures", {})
    
    # Find cubes and trays by color
    cubes = {name: obj for name, obj in objects.items() if obj.get("shape") == "cube"}
    trays = {name: fix for name, fix in fixtures.items() if fix.get("kind") == "tray"}
    
    # Pair by color
    for cube_name, cube in cubes.items():
        color = cube.get("color")
        tray_name = f"{color}_tray"
        if tray_name not in trays:
            robot.log(f"No tray for color {color}")
            continue
        
        tray = trays[tray_name]
        success = _move_cube_to_tray(robot, cube_name, cube, tray_name, tray)
        if not success:
            robot.log(f"Failed to move {cube_name} to {tray_name}")
            return False
    
    return True


def _move_cube_to_tray(robot, cube_name, cube, tray_name, tray):
    """Pick up cube and place into tray. Returns True on success."""
    cube_pos = cube["pos"]
    cube_yaw = cube["yaw"]
    tray_pos = tray["pos"]
    tray_half = tray["inner_half_size"]
    wall_h = tray["wall_height"]
    
    # Target heights
    cube_z = cube_pos[2]          # ~0.015 on table
    approach_z = 0.10             # safe travel height
    grasp_z = cube_z              # tool point at cube center for grasp
    lift_z = 0.12                 # lift above tray walls
    place_z = wall_h + 0.015      # tray floor + cube half-height = 0.025 + 0.015 = 0.04
    
    # XY targets
    cube_xy = (cube_pos[0], cube_pos[1])
    tray_xy = (tray_pos[0], tray_pos[1])
    
    # 1. Move above cube
    try:
        robot.move_to(cube_xy[0], cube_xy[1], approach_z, yaw=cube_yaw, speed=0.15)
    except MotionError:
        robot.log(f"Cannot reach above {cube_name}")
        return False
    
    # 2. Lower to grasp height
    try:
        robot.move_to(cube_xy[0], cube_xy[1], grasp_z, yaw=cube_yaw, speed=0.05)
    except MotionError:
        robot.log(f"Cannot reach grasp pose for {cube_name}")
        return False
    
    # 3. Grasp with retry
    for attempt in range(2):
        if robot.grasp():
            if robot.holding() == cube_name:
                break
            else:
                robot.release()
        robot.log(f"Grasp attempt {attempt+1} failed for {cube_name}")
        # Small wiggle and retry
        robot.move_by(dz=0.01, speed=0.05)
        robot.move_by(dz=-0.01, speed=0.05)
    else:
        robot.log(f"Failed to grasp {cube_name} after retries")
        return False
    
    # 4. Lift cube
    try:
        robot.move_to(cube_xy[0], cube_xy[1], lift_z, yaw=cube_yaw, speed=0.10)
    except MotionError:
        robot.log(f"Cannot lift {cube_name}")
        robot.release()
        return False
    
    # 5. Move above tray center
    try:
        robot.move_to(tray_xy[0], tray_xy[1], lift_z, yaw=0.0, speed=0.15)
    except MotionError:
        robot.log(f"Cannot reach above {tray_name}")
        robot.release()
        return False
    
    # 6. Lower into tray
    try:
        robot.move_to(tray_xy[0], tray_xy[1], place_z, yaw=0.0, speed=0.05)
    except MotionError:
        robot.log(f"Cannot lower into {tray_name}")
        robot.release()
        return False
    
    # 7. Release
    robot.release()
    robot.wait(0.2)
    
    # 8. Retract slightly to avoid knocking
    try:
        robot.move_by(dz=0.05, speed=0.10)
    except MotionError:
        pass
    
    # Verify: re-observe and check cube is in tray (rough check)
    obs = robot.observe()
    held = robot.holding()
    if held == cube_name:
        robot.log(f"Still holding {cube_name} after release")
        return False
    
    return True
