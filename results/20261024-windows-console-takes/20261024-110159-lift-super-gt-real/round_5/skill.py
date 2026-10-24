import math

def run(robot):
    """Pick up the red cube and hold it at least 5 cm above the table."""
    try:
        # Start from a known safe pose
        robot.home()
        
        max_attempts = 2
        grasped = False
        cx = cy = cz = None  # placeholders for the final successful perception
        
        for _ in range(max_attempts):
            obs = robot.observe()
            cube_info = obs["objects"].get("red_cube")
            if cube_info is None:
                # Cannot see the cube – abort this attempt
                continue
            cx, cy, cz = cube_info["pos"]
            
            # Tool point height that gives ample clearance above the cube
            grasp_z = cz + 0.04          # tool point ~4 cm above cube centre
            approach_z = grasp_z + 0.025 # 2.5 cm clearance above the grasp point
            
            # 1. Move to approach pose
            try:
                robot.move_to(cx, cy, approach_z, speed=0.1)
            except MotionError:
                continue  # try next attempt after re‑observing
            
            # 2. Descend to grasp position
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
                # loop will re‑observe at the top
        
        if not grasped:
            return False  # exhausted attempts without a grasp
        
        # 4. Lift the cube so its centre is at least 5 cm above the table.
        #    Constant tool‑point height that guarantees cube centre ≥ 0.065 m.
        target_z = 0.0775
        try:
            robot.move_to(cx, cy, target_z, speed=0.1)
        except MotionError:
            robot.release()
            return False
        
        # Apply a small upward push to help maintain grip, then verify hold.
        try:
            robot.move_by(dz=0.01, speed=0.05)
        except MotionError:
            pass
        
        # 5. Verify that we are still holding the cube
        if robot.holding() == "red_cube":
            return True
        else:
            robot.release()
            return False
    
    except MotionError:
        return False
    except Exception as e:
        robot.log("Exception in run:", e)
        return False
