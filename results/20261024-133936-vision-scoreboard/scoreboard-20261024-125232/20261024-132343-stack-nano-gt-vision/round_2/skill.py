# skill module
def run(robot):
    """
    Stack the red cube on top of the blue cube and release it.
    Return True on success, False otherwise.
    """

    # ------------------------------------------------------------------
    # 1. Perceive the scene
    # ------------------------------------------------------------------
    obs = robot.observe()
    objects = obs.get("objects", {})
    red_cube = blue_cube = None

    for name, data in objects.items():
        if data.get("color") == "red" and data.get("shape") == "cube":
            red_cube = data
        elif data.get("color") == "blue" and data.get("shape") == "cube":
            blue_cube = data

    if red_cube is None or blue_cube is None:
        robot.log("Target cubes not found")
        return False

    # ------------------------------------------------------------------
    # 2. Compute stacking geometry
    # ------------------------------------------------------------------
    cube_size = red_cube["size"][0]          # side length (assumed equal)
    half_size = cube_size / 2.0

    # Target centre of the red cube when stacked on the blue cube
    tx, ty = blue_cube["pos"][0], blue_cube["pos"][1]
    tz = blue_cube["pos"][2] + cube_size      # centre of red on top of blue

    # Safe approach height above the red cube (a few cm above its centre)
    approach_z = red_cube["pos"][2] + half_size + 0.02

    # ------------------------------------------------------------------
    # 3. Approach the red cube
    # ------------------------------------------------------------------
    try:
        robot.log("Moving to approach pose")
        robot.move_to(red_cube["pos"][0], red_cube["pos"][1], approach_z, speed=0.07)
    except Exception:
        robot.log("Approach move failed")
        return False

    # ------------------------------------------------------------------
    # 4. Descend to grasp height and align orientation
    # ------------------------------------------------------------------
    try:
        robot.log("Descending to grasp height")
        # Position the tool point at the cube centre (fingers will be around its middle)
        robot.move_to(red_cube["pos"][0], red_cube["pos"][1], red_cube["pos"][2], speed=0.07)
        # Optional: orient fingers with the cube's yaw for a more stable grasp
        robot.move_to(red_cube["pos"][0], red_cube["pos"][1], red_cube["pos"][2],
                      yaw=red_cube["yaw"], speed=0.07)
    except Exception:
        robot.log("Grasp descent failed")
        return False

    # ------------------------------------------------------------------
    # 5. Grasp the red cube
    # ------------------------------------------------------------------
    robot.log("Closing grasp")
    robot.open()                     # ensure fingers are open
    robot.grasp()

    # Verify that the cube is actually held
    if robot.holding() != "red_cube":
        robot.log("Grasp verification failed")
        return False

    # ------------------------------------------------------------------
    # 6. Lift clear of the blue cube
    # ------------------------------------------------------------------
    lift_z = tz + 0.02                # clearance above the target centre
    try:
        robot.log("Lifting the cube")
        robot.move_to(tx, ty, lift_z, speed=0.07)
    except Exception:
        robot.log("Lift move failed")
        return False

    # ------------------------------------------------------------------
    # 7. Descend to target centre and release
    # ------------------------------------------------------------------
    try:
        robot.log("Descending to target centre")
        robot.move_to(tx, ty, tz, speed=0.07)
    except Exception:
        robot.log("Target descent failed")
        return False

    robot.log("Releasing")
    robot.release()

    # ------------------------------------------------------------------
    # 8. Optional safe retreat and signal completion
    # ------------------------------------------------------------------
    robot.log("Task completed")
    return True
