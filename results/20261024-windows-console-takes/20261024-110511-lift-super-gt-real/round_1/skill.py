import math

def run(robot):
    """Pick up the red cube and hold it ≥5 cm above the table."""
    max_attempts = 3
    for attempt in range(max_attempts):
        # 1️⃣ Observe the scene to get the cube pose
        obs = robot.observe()
        cube_info = obs.get("objects", {}).get("red_cube")
        if not cube_info:
            # Cube not seen – try again after a brief wait
            robot.wait(0.1)
            continue

        # Extract pose (centre of cube) and its yaw
        cx, cy, cz = cube_info["pos"]
        cyaw = cube_info["yaw"]

        # Desired heights (table surface is at z=0, cube centre rests at ~0.015 m)
        grasp_z = cz + 0.015   # finger pads around the middle of the cube
        lift_z  = cz + 0.065   # 5 cm above table (0.015 + 0.05)

        # 2️⃣ Move to a safe clearance above the cube
        try:
            robot.move_to(cx, cy, cz + 0.08, yaw=cyaw, speed=0.1)
        except Exception:  # MotionError or similar
            continue  # retry with fresh observation

        # 3️⃣ Descend to the grasp position
        try:
            robot.move_to(cx, cy, grasp_z, yaw=cyaw, speed=0.05)
        except Exception:
            continue

        # 4️⃣ Attempt to grasp
        if not robot.grasp():
            # Grasp failed – release (just in case) and retry
            robot.release()
            continue

        # 5️⃣ Verify we are actually holding something
        if robot.holding() != "red_cube":
            robot.release()
            continue

        # 6️⃣ Lift the cube to the target height
        try:
            robot.move_to(cx, cy, lift_z, yaw=cyaw, speed=0.1)
        except Exception:
            # If lift fails, release and try again
            robot.release()
            continue

        # 7️⃣ Final verification: check height of the held cube
        final_pose = robot.get_pose("red_cube")
        if final_pose is not None and final_pose["pos"][2] >= 0.06:  # ≥5 cm above table
            return True  # Success

        # Something went wrong (e.g., slip) – release and retry
        robot.release()

    # Exhausted attempts without success
    return False
