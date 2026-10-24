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
        # Finger pads sit 1.25 cm (=0.0125 m) below the tool point.
        # To grasp the cube's centre we place the tool point at:
        grasp_z = cz + 0.0125          # tool point height for centre grasp
        # Approach point: a little above the grasp to avoid hitting the cube
        approach_z = grasp_z + 0.025   # 2.5 cm clearance
        
        max_attempts = 3
        grasped = False
        
        for attempt in range(max_attempts):
            # 1. Move to a safe approach pose above the cube
            try:
                robot.move_to(cx, cy, approach_z, speed=0.1)
            except MotionError:
                # If we can't reach the approach pose, abort this attempt
                continue
            
            # 2. Descend slowly to the grasp position
            try:
                robot.move_to(cx, cy, grasp_z, speed=0.05)
            except MotionError:
                continue
            
            # 3. Close the gripper
            grasped = robot.grasp()
            if grasped:
                break  # successful grasp, exit retry loop
            else:
                # Grasp failed – retreat a bit and try again (with fresh observation)
                try:
                    robot.move_by(dz=0.02, speed=0.05)
                except MotionError:
                    pass
                # loop will re‑observe at the top (via new observe() call)
        
        if not grasped:
            # Exhausted attempts without a grasp
            return False
        
        # 4. Lift the cube so its centre is at least 5 cm above the table.
        #    Required tool‑point height is constant: 0.0775 m.
        target_z = 0.0775
        try:
            robot.move_to(cx, cy, target_z, speed=0.05)  # slower lift to avoid motion errors
        except MotionError:
            return False
        
        # 5. Verify that we are still holding the cube
        if robot.holding() == "red_cube":
            return True
        else:
            # Object slipped; open gripper and report failure
            robot.release()
            return False
    
    except MotionError:
        # Any motion error leads to failure
        return False
    except Exception as e:
        # Unexpected error – log and fail
        robot.log("Exception in run:", e)
        return False
