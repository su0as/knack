import math

def run(robot):
    # Perceive scene
    obs = robot.observe()
    yellow = obs["objects"].get("yellow_cube")
    tray = obs["fixtures"].get("tray")
    if not yellow or not tray:
        robot.log("Missing yellow cube or tray")
        return False

    cube_pos = yellow["pos"]
    cube_yaw = yellow["yaw"]
    tray_pos = tray["pos"]
    inner_half = tray["inner_half_size"]

    # Target positions
    # Grasp: approach from above, align fingers with cube yaw
    grasp_xy = (cube_pos[0], cube_pos[1])
    grasp_z = 0.015  # cube center height
    # Place: tray center, same height to set cube on tray bottom
    place_xy = (tray_pos[0], tray_pos[1])
    place_z = 0.015

    # 1. Move above cube (safe height)
    try:
        robot.move_to(grasp_xy[0], grasp_xy[1], 0.12, yaw=cube_yaw, speed=0.15)
    except Exception as e:
        robot.log(f"Move above cube failed: {e}")
        return False

    # 2. Lower to grasp height
    try:
        robot.move_to(grasp_xy[0], grasp_xy[1], grasp_z, yaw=cube_yaw, speed=0.05)
    except Exception as e:
        robot.log(f"Lower to cube failed: {e}")
        return False

    # 3. Grasp
    if not robot.grasp():
        robot.log("Grasp failed")
        return False
    if robot.holding() != "yellow_cube":
        robot.log("Not holding yellow cube")
        robot.release()
        return False

    # 4. Lift cube clear of table
    try:
        robot.move_to(grasp_xy[0], grasp_xy[1], 0.12, yaw=cube_yaw, speed=0.10)
    except Exception as e:
        robot.log(f"Lift cube failed: {e}")
        robot.release()
        return False

    # 5. Move above tray center
    try:
        robot.move_to(place_xy[0], place_xy[1], 0.12, yaw=0.0, speed=0.15)
    except Exception as e:
        robot.log(f"Move above tray failed: {e}")
        robot.release()
        return False

    # 6. Lower into tray
    try:
        robot.move_to(place_xy[0], place_xy[1], place_z, yaw=0.0, speed=0.05)
    except Exception as e:
        robot.log(f"Lower into tray failed: {e}")
        robot.release()
        return False

    # 7. Release
    robot.release()
    robot.wait(0.2)

    # Verify release
    if robot.holding() is not None:
        robot.log("Still holding after release")
        return False

    robot.home()
    return True
