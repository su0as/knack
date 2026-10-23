import math

def run(robot):
    """
    Pick up the red cube and hold it at least 5 cm above the table.
    Returns True if the cube is successfully grasped and lifted, False otherwise.
    """
    try:
        # Start from a known safe pose
        robot.home()
        
        # Get the current pose of the red cube
        obs = robot.observe()
        cube_info = obs["objects"].get("red_cube")
        if cube_info is None:
            robot.log("Red cube not found in observation")
            return False
        
        # Extract position (center of cube)
        cx, cy, cz = cube_info["pos"]
        # Cube half-size (assuming cube shape); fallback if size missing
        size = cube_info.get("size")
        if size is None or len(size) == 0:
            robot.log("Cube size missing, using default 0.03 m")
            half_size = 0.015
        else:
            half_size = size[0] / 2.0  # all sides equal for a cube
        
        # Desired grasp height: center of cube (finger pads around mid-height)
        grasp_z = cz
        
        # Approach pose: above the cube, safe clearance
        approach_z = grasp_z + 0.08  # 8 cm above center
        
        # Move to approach position (above the cube)
        move_approach = robot.move_to(cx, cy, approach_z, speed=0.2)
        if not move_approach["ok"]:
            robot.log("Failed to move to approach position")
            return False
        
        # Move down to grasp height (slow for precision)
        move_down = robot.move_to(cx, cy, grasp_z, speed=0.07)
        if not move_down["ok"]:
            robot.log("Failed to move to grasp position")
            return False
        
        # Close the gripper to grasp
        grasped = robot.grasp()
        if not grasped:
            robot.log("Grasp attempt returned False")
            return False
        
        # Verify that we are actually holding the red cube
        if robot.holding() != "red_cube":
            robot.log("Not holding red cube after grasp")
            return False
        
        # Lift the cube to a safe height (at least 5 cm above table)
        # Table is at z=0, so bottom clearance of 0.05 requires center height = 0.05 + half_size
        lift_z = 0.05 + half_size + 0.001  # small margin for simulation variation
        move_up = robot.move_to(cx, cy, lift_z, speed=0.15)
        if not move_up["ok"]:
            robot.log("Failed to lift cube")
            return False
        
        # Hold briefly to demonstrate stability
        robot.wait(0.5)
        
        # Success
        robot.log("Red cube lifted successfully")
        return True
    
    except Exception as e:
        # Catch unexpected errors (e.g., MotionError) and fail gracefully
        robot.log(f"Exception during execution: {e}")
        return False
