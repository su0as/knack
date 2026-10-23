import math

def run(robot):
    """Stack the red cube on top of the blue cube."""
    try:
        # Start from a known safe pose
        robot.home()

        # Observe the scene to get current poses
        obs = robot.observe()
        red_pose = obs['objects']['red_cube']
        blue_pose = obs['objects']['blue_cube']

        def grasp_cube(pose, desc=""):
            """Grasp a cube given its pose dictionary."""
            cx, cy, cz = pose['pos']
            yaw = pose['yaw']
            size = pose['size']          # [x, y, z] dimensions
            half_z = size[2] / 2.0       # half height of the cube
            epsilon = 0.005              # small clearance above the centre

            # Safety offset above the cube for approach
            approach_z = cz + half_z + epsilon + 0.05   # a bit higher than grasp point
            # Desired grasp point (a little above the cube centre)
            grasp_z = cz + half_z + epsilon

            # Approach from above
            robot.move_to(cx, cy, approach_z, yaw=yaw, speed=0.15)

            # Descend to grasp height
            robot.move_to(cx, cy, grasp_z, yaw=yaw, speed=0.05)

            # Close the fingers
            if not robot.grasp():
                # Retreat a bit and try once more
                robot.move_by(dz=0.05, speed=0.05)
                if not robot.grasp():
                    robot.log(f"Failed to grasp {desc}")
                    return False
            robot.log(f"Grasped {desc}")

            # Lift a little to clear the table (small clearance)
            robot.move_by(dz=0.02, speed=0.10)
            return True

        # --- Grasp the red cube ---
        if not grasp_cube(red_pose, "red cube"):
            return False

        # --- Get current gripper pose after grasp and small lift ---
        obs2 = robot.observe()
        grip = obs2['gripper']
        cur_x, cur_y, cur_z = grip['pos']

        # --- Move to a height suitable for horizontal movement (just above red cube top) ---
        red_top_z = red_pose['pos'][2] + red_pose['size'][2] / 2.0 + 0.01
        try:
            robot.move_to(cur_x, cur_y, red_top_z, speed=0.15)
        except Exception as e:
            robot.log(f"Failed to move to horizontal height: {e}")
            try:
                robot.move_to(cur_x, cur_y, red_top_z, speed=0.05)
            except Exception as e2:
                robot.log(f"Still failed to reach horizontal height: {e2}")
                return False

        # --- Compute horizontal offset from red to blue cube using current red pose ---
        red_current = robot.get_pose('red_cube')
        dx = blue_pose['pos'][0] - red_current['pos'][0]
        dy = blue_pose['pos'][1] - red_current['pos'][1]

        # --- Move horizontally at the current height ---
        try:
            robot.move_by(dx, dy, speed=0.15)
        except Exception as e:
            robot.log(f"Horizontal move failed: {e}")
            # Fallback: explicit move_to at same height
            try:
                robot.move_to(
                    red_current['pos'][0] + dx,
                    red_current['pos'][1] + dy,
                    red_current['pos'][2],
                    speed=0.15,
                )
            except Exception as e2:
                robot.log(f"Fallback horizontal move failed: {e2}")
                return False

        # --- Compute target tool‑point height for proper stacking ---
        h_red = red_pose['size'][2]          # cube height (unchanged)
        epsilon = 0.005
        # Tool point must be above the red cube centre by:
        #   (grasp_z - red_z) + lift_after_grasp = half_z + epsilon + 0.02
        # Desired red cube centre = blue_z + h_red (sit on top of blue cube)
        # Hence target_z_tool = blue_z + h_red + (half_z + epsilon + 0.02)
        # Simplified: target_z_tool = blue_z + 1.5*h_red + epsilon + 0.02
        target_z_tool = blue_pose['pos'][2] + 1.5 * h_red + epsilon + 0.02

        # Cap at a safe maximum reachable height (empirically ~0.245 m)
        MAX_Z = 0.245
        if target_z_tool > MAX_Z:
            target_z_tool = MAX_Z
        # Ensure we stay above the table
        MIN_Z = 0.02
        if target_z_tool < MIN_Z:
            target_z_tool = MIN_Z

        # --- Move to the stacking height ---
        obs3 = robot.observe()
        grip2 = obs3['gripper']
        cur_x2, cur_y2, cur_z2 = grip2['pos']
        try:
            robot.move_to(cur_x2, cur_y2, target_z_tool, speed=0.05)
        except Exception as e:
            robot.log(f"Vertical move to stack height failed: {e}")
            try:
                robot.move_to(cur_x2, cur_y2, target_z_tool, speed=0.02)
            except Exception as e2:
                robot.log(f"Still failed to reach stack height: {e2}")
                return False

        # --- Release the red cube onto the blue one ---
        robot.release()
        robot.log("Released red cube onto blue cube")
        robot.wait(0.2)   # allow the cube to settle

        # --- Retreat to a safe height ---
        try:
            robot.move_by(dz=0.10, speed=0.10)
        except Exception as e:
            robot.log(f"Retreat failed: {e}")

        # Optional: return home
        try:
            robot.home()
        except Exception:
            pass

        return True

    except Exception as e:
        robot.log(f"Exception: {e}")
        try:
            robot.home()
        except Exception:
            pass
        return False
