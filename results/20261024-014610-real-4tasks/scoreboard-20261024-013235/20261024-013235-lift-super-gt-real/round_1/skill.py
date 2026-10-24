import math

def run(robot):
    """Pick up the red cube and hold it at least 5 cm above the table."""
    # Safety: start from a known good pose
    robot.home()

    max_attempts = 3
    for attempt in range(max_attempts):
        # Fresh perception
        obs = robot.observe()
        cube_info = obs["objects"].get("red_cube")
        if cube_info is None:
            robot.log("Red cube not observed")
            return False

        # Extract pose (centre of cube)
        cx, cy, cz = cube_info["pos"]
        # Optional: use yaw to align fingers, but not required for a cube
        cyaw = cube_info.get("yaw", 0.0)

        # 1. Move to a safe approach point above the cube
        approach_z = cz + 0.05  # 5 cm above cube centre
        try:
            robot.move_to(cx, cy, approach_z, yaw=cyaw, speed=0.15)
        except Exception as e:
            robot.log(f"Move to approach failed: {e}")
            continue  # retry with fresh observation

        # 2. Descend to grasp height (aim for cube centre)
        try:
            robot.move_to(cx, cy, cz, yaw=cyaw, speed=0.07)
        except Exception as e:
            robot.log(f"Descend to grasp failed: {e}")
            continue

        # 3. Attempt to grasp
        if robot.grasp():
            # Verify grasp
            if robot.holding() == "red_cube":
                robot.log("Grasp successful")
                break  # exit retry loop
            else:
                robot.log("Grasp returned True but not holding")
                robot.release()
        else:
            robot.log("Grasp returned False")
        # If we get here, grasp failed; lift slightly and try again
        try:
            robot.move_by(dz=0.02, speed=0.07)  # small retreat
        except Exception:
            pass
        robot.release()
    else:
        # Exhausted attempts
        robot.log("Failed to grasp red cube after multiple attempts")
        return False

    # 4. Lift the cube to at least 5 cm above the table
    # Current tool point is roughly at cube centre (cz ≈ 0.015). Add 0.05 m.
    target_z = cz + 0.05
    try:
        robot.move_to(cx, cy, target_z, yaw=cyaw, speed=0.15)
    except Exception as e:
        robot.log(f"Lift failed: {e}")
        # Even if lift fails, check if we are already high enough
        current_pose = robot.get_pose("red_cube") if robot.holding() else None
        if current_pose and current_pose["pos"][2] >= 0.065:
            return True
        return False

    # Final verification: ensure we are still holding and high enough
    held = robot.holding()
    if held == "red_cube":
        # Get latest pose to check height
        pose = robot.get_pose("red_cube")
        if pose and pose["pos"][2] >= 0.065:  # 5 cm above table (centre ≥ 0.015+0.05)
            robot.log("Task succeeded: red cube held ≥5 cm above table")
            return True
        else:
            robot.log(f"Cube too low: z={pose['pos'][2] if pose else 'None'}")
            return False
    else:
        robot.log("Lost grasp during lift")
        return False
