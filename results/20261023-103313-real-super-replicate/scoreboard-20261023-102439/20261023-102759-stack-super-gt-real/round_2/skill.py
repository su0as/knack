import math

def run(robot):
    """Stack the red cube on top of the blue cube."""
    SAFE_Z = 0.15          # travel height above the table
    MAX_ATTEMPTS = 3       # how many full pick‑and‑place cycles we try
    POS_TOL = 0.02         # 2 cm tolerance for verification

    def safe_move(**kwargs):
        """Wrapper around robot.move_to/move_by that catches MotionError."""
        try:
            # Determine whether to call move_to or move_by
            if 'x' in kwargs:
                res = robot.move_to(**kwargs)
            else:
                res = robot.move_by(**kwargs)
            return res.get('ok', False)
        except Exception:   # MotionError or any other unexpected error
            return False

    for attempt in range(MAX_ATTEMPTS):
        robot.log(f"Attempt {attempt+1}/{MAX_ATTEMPTS}")
        robot.home()
        # Let vision settle before reading poses
        robot.wait(0.5)

        # --- 1. Perceive current cube poses ---
        obs = robot.observe()
        red_obj = obs['objects'].get('red_cube')
        blue_obj = obs['objects'].get('blue_cube')
        if not red_obj or not blue_obj:
            robot.log("Could not see both cubes")
            continue

        red_pos = red_obj['pos']
        blue_pos = blue_obj['pos']
        red_yaw = red_obj['yaw']

        # --- 2. Move above red cube ---
        above_red = [red_pos[0], red_pos[1], SAFE_Z]
        if not safe_move(x=above_red[0], y=above_red[1], z=above_red[2], yaw=red_yaw):
            robot.log("Failed to move above red cube")
            continue

        # --- 3. Descend to grasp height (center of red cube (center) ---
        grasp_pos = [red_pos[0], red_pos[1], red_pos[2]]
        if not safe_move(x=grasp_pos[0], y=grasp_pos[1], z=grasp_pos[2],
                         yaw=red_yaw, speed=0.05):
            robot.log("Failed to descend to grasp red cube")
            continue

        # --- 3b. Lift slightly to avoid interference during grasp ---
        if not safe_move(dz=0.02, speed=0.05):
            robot.log("Failed to lift slightly before grasp")
            continue

        # --- 4. Grasp (may need a couple tries) ---
        grasped = False
        for _ in range(2):
            if robot.grasp():
                if robot.holding() == 'red_cube':
                    grasped = True
                    break
            robot.log("Grasp did not hold red cube, releasing and retrying")
            robot.release()
            robot.wait(0.05)
        if not grasped:
            robot.log("Unable to grasp red cube after retries")
            # retreat a bit before next attempt
            safe_move(dz=0.04, speed=0.05)
            continue

        # --- 5. Lower to grasp center (optional, ensures secure hold) ---
        if not safe_move(x=grasp_pos[0], y=grasp_pos[1], z=grasp_pos[2],
                         yaw=red_yaw, speed=0.05):
            robot.log("Failed to lower to grasp center")
            robot.release()
            continue

        # --- 6. Lift red cube to safe height ---
        lift_pos = [red_pos[0], red_pos[1], SAFE_Z]
        if not safe_move(x=lift_pos[0], y=lift_pos[1], z=lift_pos[2],
                         yaw=red_yaw, speed=0.05):
            robot.log("Failed to lift red cube")
            robot.release()
            continue

        # --- 7. Move above blue cube ---
        above_blue = [blue_pos[0], blue_pos[1], SAFE_Z]
        if not safe_move(x=above_blue[0], y=above_blue[1], z=above_blue[2]):
            robot.log("Failed to move above blue cube")
            robot.release()
            continue

        # --- 8. Descend to place height (red centre on blue centre) ---
        # Increased clearance to avoid collision with the blue cube during descent
        place_z = blue_pos[2] + 0.05
        place_pos = [blue_pos[0], blue_pos[1], place_z]
        if not safe_move(x=place_pos[0], y=place_pos[1], z=place_pos[2],
                         speed=0.05):
            robot.log("Failed to descend to place position")
            robot.release()
            continue

        # --- 9. Release ---
        robot.release()
        robot.wait(0.2)

        # --- 10. Verify stacking ---
        obs2 = robot.observe()
        red2 = obs2['objects'].get('red_cube')
        if red2:
            dx = red2['pos'][0] - place_pos[0]
            dy = red2['pos'][1] - place_pos[1]
            dz = red2['pos'][2] - place_pos[2]
            if abs(dx) < POS_TOL and abs(dy) < POS_TOL and abs(dz) < POS_TOL:
                robot.log("Stack successful")
                return True
            else:
                robot.log(f"Red cube misplaced: dx={dx:.3f}, dy={dy:.3f}, dz={dz:.3f}")
        else:
            robot.log("Red cube disappeared after release")

        # If verification failed, loop for another attempt (robot will re‑home)
    robot.log("All attempts exhausted")
    return False
