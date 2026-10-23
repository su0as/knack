import math

def run(robot):
    """Stack the red cube on top of the blue cube."""
    SAFE_Z = 0.15          # travel height above the table
    MAX_ATTEMPTS = 3       # how many full pick‑and‑place cycles we try
    POS_TOL = 0.03         # 3 cm tolerance for verification
    APPROACH_OFFSET = 0.02 # meters above cube center for pre‑grasp approach
    MAX_PLACE_RETRIES = 2  # retries for the descent to place height

    def clamp_z(z):
        """Clamp z to the safe vertical workspace [0.010, 0.26]."""
        if z < 0.010:
            return 0.010
        if z > 0.26:
            return 0.26
        return z

    def safe_move_to(**kwargs):
        """
        Wrapper around robot.move_to that clamps the z coordinate
        and catches MotionError (or any other exception).
        Returns True if the motion reports ok, False otherwise.
        """
        try:
            if 'z' in kwargs:
                kwargs['z'] = clamp_z(kwargs['z'])
            res = robot.move_to(**kwargs)
            return res.get('ok', False)
        except Exception:
            return False

    for attempt in range(MAX_ATTEMPTS):
        robot.log(f"Attempt {attempt+1}/{MAX_ATTEMPTS}")
        robot.home()
        robot.wait(0.2)  # let vision settle

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

        # --- 2. Move above red cube (safe height) ---
        above_red = [red_pos[0], red_pos[1], SAFE_Z]
        if not safe_move_to(x=above_red[0], y=above_red[1], z=above_red[2], yaw=red_yaw):
            robot.log("Failed to move above red cube")
            continue

        # --- 3. Pre‑grasp: move to a point just above the cube center ---
        pre_grasp_z = clamp_z(red_pos[2] + APPROACH_OFFSET)
        pre_grasp_pos = [red_pos[0], red_pos[1], pre_grasp_z]
        if not safe_move_to(x=pre_grasp_pos[0], y=pre_grasp_pos[1], z=pre_grasp_pos[2],
                            yaw=red_yaw, speed=0.05):
            robot.log("Failed to move to pre‑grasp position")
            continue

        # --- 4. Descend to grasp height (center of red cube) ---
        grasp_z = clamp_z(red_pos[2])
        grasp_pos = [red_pos[0], red_pos[1], grasp_z]
        if not safe_move_to(x=grasp_pos[0], y=grasp_pos[1], z=grasp_pos[2],
                            yaw=red_yaw, speed=0.05):
            robot.log("Failed to descend to grasp red cube")
            continue

        # --- 5. Grasp (may need a couple tries) ---
        grasped = False
        for _ in range(2):
            if robot.grasp():
                if robot.holding() == 'red_cube':
                    grasped = True
                    break
            # grasp didn't hold the cube
            robot.log("Grasp did not hold red cube, releasing and retrying")
            robot.release()
            robot.wait(0.05)
            # Retreat to a safe height before trying again
            retreat_pos = [red_pos[0], red_pos[1], SAFE_Z]
            if not safe_move_to(x=retreat_pos[0], y=retreat_pos[1], z=retreat_pos[2],
                                yaw=red_yaw, speed=0.05):
                robot.log("Failed to retreat after grasp attempt")
                break
        if not grasped:
            robot.log("Unable to grasp red cube after retries")
            # Ensure we are at a safe height before next attempt
            safe_move_to(x=red_pos[0], y=red_pos[1], z=SAFE_Z, yaw=red_yaw, speed=0.05)
            continue

        # --- 6. Lift red cube to safe height ---
        lift_pos = [red_pos[0], red_pos[1], SAFE_Z]
        if not safe_move_to(x=lift_pos[0], y=lift_pos[1], z=lift_pos[2],
                            yaw=red_yaw, speed=0.05):
            robot.log("Failed to lift red cube")
            robot.release()
            continue

        # --- 7. Move above blue cube ---
        above_blue = [blue_pos[0], blue_pos[1], SAFE_Z]
        if not safe_move_to(x=above_blue[0], y=above_blue[1], z=above_blue[2]):
            robot.log("Failed to move above blue cube")
            robot.release()
            continue

        # --- 8. Re‑perceive blue cube after waiting (avoid joint‑limit surprises) ---
        robot.wait(0.1)
        obs_check = robot.observe()
        blue_check = obs_check['objects'].get('blue_cube')
        if blue_check:
            # If the blue cube moved more than 5 mm, update our target
            if (abs(blue_check['pos'][0] - blue_pos[0]) > 0.005 or
                abs(blue_check['pos'][1] - blue_pos[1]) > 0.005):
                robot.log("Blue cube moved, updating target")
                blue_pos = blue_check['pos']

        # --- 9. Descend to place height with retries ---
        # Desired centre height when stacked: blue centre + cube side length (~0.030)
        # Add a small clearance (0.005 m) to avoid collision during descent.
        place_z = clamp_z(blue_pos[2] + 0.030 + 0.005)  # blue centre + 0.035 m
        place_pos = [blue_pos[0], blue_pos[1], place_z]

        place_success = False
        for place_try in range(MAX_PLACE_RETRIES):
            if safe_move_to(x=place_pos[0], y=place_pos[1], z=place_pos[2],
                            speed=0.05):
                place_success = True
                break
            else:
                robot.log(f"Place descent attempt {place_try+1} failed, retreating to safe height")
                retreat_pos = [blue_pos[0], blue_pos[1], SAFE_Z]
                # Try to retreat; if this also fails we still continue to next try
                safe_move_to(x=retreat_pos[0], y=retreat_pos[1], z=retreat_pos[2],
                             speed=0.05)
        if not place_success:
            robot.log("Failed to reach place height after retries")
            robot.release()
            continue

        # --- 10. Release ---
        robot.release()
        robot.wait(0.2)

        # --- 11. Optional nudge to ensure proper seating ---
        # Move slowly back to the intended place position to let the cube settle.
        if not safe_move_to(x=place_pos[0], y=place_pos[1], z=place_pos[2],
                            speed=0.05):
            robot.log("Failed to nudge after release")

        # --- 12. Verify stacking ---
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
