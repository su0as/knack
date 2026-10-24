import math

def run(robot):
    """Pick up the red cube and hold it at least 5 cm above the table."""
    try:
        # Start from a known safe pose
        robot.home()
        
        # Perceive the scene once
        obs = robot.observe()
        cube_info = obs["objects"].get("red_cube")
        if cube_info is None:
            # If we can't see the cube, we cannot succeed
            return False
        
        # Extract cube centre position
        cx, cy, cz = cube_info["pos"]
        # The cube's half‑height is size[2]/2 = 0.015 m (from the example)
        # Finger pads sit 1.25 cm (=0.0125 m) below the tool point.
        # To grasp the cube's centre we place the tool point at:
        grasp_z = cz + 0.0125
        
        # Approach point: a little above the grasp to avoid hitting the cube
        approach_z = grasp_z + 0.03  # 3 cm clearance
        
        # 1. Move to a safe approach pose above the cube
        robot.move_to(cx, cy, approach_z, speed=0.1)
        
        # 2. Descend slowly to the grasp position
        robot.move_to(cx, cy, grasp_z, speed=0.05)
        
        # 3. Close the gripper
        grasped = robot.grasp()
        if not grasped:
            # Grasp failed – retreat and report failure
            robot.move_by(dz=0.02, speed=0.05)  # small retreat
            return False
        
        # 4. Lift the cube at least 5 cm above the table.
        #    We lift by a fixed 5 cm from the current tool point.
        robot.move_by(dz=0.05, speed=0.1)
        
        # 5. Verify that we are still holding the cube
        if robot.holding() == "red_cube":
            return True
        else:
            # Object slipped; try a quick re‑grasp attempt (optional)
            robot.release()
            return False
    
    except Exception as e:
        # Any unexpected error (including MotionError) leads to failure
        # Optionally log for debugging
        robot.log("Exception in run:", e)
        return False
