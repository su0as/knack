import math

def run(robot):
    try:
        # Start from a safe pose
        robot.home()

        # Observe the scene to get the yellow cube and tray poses
        obs = robot.observe()
        cube_info = obs['objects'].get('yellow_cube')
        tray_info = obs['fixtures'].get('tray')
        if not cube_info or not tray_info:
            robot.log("Missing cube or tray in observation")
            return False

        # Extract poses
        cx, cy, cz = cube_info['pos']
        cyaw = cube_info['yaw']
        tx, ty, tz = tray_info['pos']   # tray sits on the table (z = 0)

        # --- Grasping sequence ---
        # Move above the cube
        above_z = cz + 0.08
        move_res = robot.move_to(cx, cy, above_z, yaw=cyaw, speed=0.15)
        if not move_res.get('ok', False):
            robot.log("Failed to move above cube")
            return False

        # Descend to a grasping height (just above the cube centre)
        grasp_z = cz + 0.02
        move_res = robot.move_to(cx, cy, grasp_z, yaw=cyaw, speed=0.05)
        if not move_res.get('ok', False):
            robot.log("Failed to move to grasp height")
            return False

        # Attempt grasp (allow one retry with improved alignment)
        grasp_success = False
        for _ in range(2):
            if robot.grasp():
                grasp_success = True
                break
            # lift higher and re‑align before trying again
            robot.move_by(dz=0.02, speed=0.05)
            robot.move_to(cx, cy, above_z, speed=0.1)          # pre‑grasp positioning
            robot.move_to(cx, cy, grasp_z, yaw=cyaw, speed=0.05) # descend to grasp height
        if not grasp_success:
            robot.log("Grasp did not detect an object")
            return False

        # Verify that we are holding the yellow cube
        if robot.holding() != 'yellow_cube':
            robot.log("Not holding the yellow cube after grasp")
            return False

        # --- Transfer to tray ---
        # Move above the tray centre
        above_tray_z = tz + 0.08
        move_res = robot.move_to(tx, ty, above_tray_z, speed=0.15)
        if not move_res.get('ok', False):
            robot.log("Failed to move above tray")
            return False

        # Verify still holding before proceeding
        if robot.holding() != 'yellow_cube':
            robot.log("Lost grasp while moving above tray")
            return False

        # Small ascent to clear tray edge before descending
        robot.move_by(dz=0.02, speed=0.05)

        # Lower to a safe placement height (cube centre resting on tray bottom with clearance)
        place_z = tz + 0.025   # half cube size + 0.01 m clearance
        move_res = robot.move_to(tx, ty, place_z, speed=0.05)
        if not move_res.get('ok', False):
            robot.log("Failed to move to placement height")
            return False

        # Verify still holding before release
        if robot.holding() != 'yellow_cube':
            robot.log("Lost grasp before release")
            return False

        # Release the cube
        robot.release()

        # Optional: verify release
        if robot.holding() is not None:
            robot.log("Still holding an object after release")
            return False

        # Success
        return True

    except Exception as e:
        # Catch any unexpected errors (e.g., MotionError) and fail safely
        robot.log(f"Exception during skill execution: {e}")
        return False
