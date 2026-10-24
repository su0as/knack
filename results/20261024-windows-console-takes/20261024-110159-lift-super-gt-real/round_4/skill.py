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
        
        # Tool point height that puts finger pads ~2 cm above the cube centre
        # and guarantees we stay clear of the table.
        grasp_z = cz + 0.02
        if grasp_z < 0.04:
            grasp_z = 0.04
        
        # Approach point: a little above the grasp to avoid hitting the cube
        approach_z = grasp_z + 0.025  # 2.5 cm clearance
        
        # Helper to attempt a grasp sequence
        def attempt_grasp():
            try:
                robot.move_to(cx, cy, approach_z, speed=0.1)
            except MotionError:
                return False
            try:
                robot.move_to(cx, cy, grasp_z, speed=0.05)
            except MotionError:
                return False
            return robot.grasp()
        
        # Try to grasp; allow one retry on failure
        grasped = attempt_grasp()
        if not grasped:
            # Small retreat before retrying
            try:
                robot.move_by(dz=0.02, speed=0.05)
            except MotionError:
                pass
            grasped = attempt_grasp()
        
        if not grasped:
            return False
        
        # Re‑observe to get the cube's actual height after grasp
        obs2 = robot.observe()
        cube_info2 = obs2["objects"].get("red_cube")
        if cube_info2 is None:
            # Lost track of the cube
            robot.release()
            return False
        _, _, cz_after = cube_info2["pos"]
        
        # Lift so that the cube centre is at least 0.065 m above the table
        target_z = cz_after + 0.065  # tool‑point height
        try:
            robot.move_to(cx, cy, target_z, speed=0.1)
        except MotionError:
            robot.release()
            return False
        
        # Final verification: still holding the cube
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
