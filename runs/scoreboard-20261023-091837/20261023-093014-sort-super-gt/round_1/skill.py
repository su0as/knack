import math

def run(robot):
    """Pick up red and blue cubes and place them into the trays of the same colour."""
    max_attempts = 2
    colours = ["red", "blue"]

    # Helper to get the name of an object given its colour and type
    def obj_name(colour, typ):
        # typ: "cube" or "tray"
        return f"{colour}_{typ}"

    for attempt in range(max_attempts):
        try:
            # Start each attempt from a known safe pose
            robot.home()
            obs = robot.observe()

            # Build lookup tables for quick access
            objects = obs.get("objects", {})
            fixtures = obs.get("fixtures", {})

            success = True

            for colour in colours:
                cube_key = obj_name(colour, "cube")
                tray_key = obj_name(colour, "tray")

                if cube_key not in objects or tray_key not in fixtures:
                    success = False
                    break

                cube_pose = objects[cube_key]
                tray_pose = fixtures[tray_key]

                cx, cy, cz = cube_pose["pos"]
                cyaw = cube_pose.get("yaw", 0.0)

                tx, ty, tz = tray_pose["pos"]  # tz is 0.0 (table top)

                # --- Pick cube ---
                # Move above cube
                above_cube_z = cz + 0.05
                robot.move_to(cx, cy, above_cube_z, yaw=cyaw, speed=0.15)
                # Lower to grasp height (centre of cube)
                robot.move_to(cx, cy, cz, yaw=cyaw, speed=0.05)
                # Close fingers
                if not robot.grasp():
                    success = False
                    break
                # Verify hold
                if robot.holding() != cube_key:
                    success = False
                    robot.release()
                    break
                # Lift up
                robot.move_by(dz=0.05, speed=0.15)

                # --- Place cube in tray ---
                # Move above tray
                safe_z = 0.05
                robot.move_to(tx, ty, safe_z, yaw=0.0, speed=0.15)
                # Lower to release height (centre of cube inside tray)
                robot.move_to(tx, ty, cz, yaw=0.0, speed=0.05)
                # Open fingers
                robot.release()
                # Small retreat
                robot.move_by(dz=0.05, speed=0.15)

            if success:
                # Final home position
                robot.home()
                return True
            else:
                # If something went wrong, reset and retry
                robot.release()
                robot.home()
                continue

        except Exception as e:
            # Catch unexpected errors, reset and retry
            robot.release()
            robot.home()
            continue

    # If we exhausted attempts without success
    robot.home()
    return False
