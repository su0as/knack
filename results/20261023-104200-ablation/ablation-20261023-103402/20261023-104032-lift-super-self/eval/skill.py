import math

def run(robot):
    # Start from a known safe pose
    robot.home()
    
    # Get the current pose of the red cube
    obs = robot.observe()
    cube_info = obs["objects"].get("red_cube")
    if cube_info is None:
        # Fallback: try to get pose by name (should still work)
        try:
            cube_pose = robot.get_pose("red_cube")
        except Exception:
            robot.log("Red cube not found in observation or get_pose")
            return False
        cube_pos = cube_pose["pos"]
        cube_yaw = cube_pose["yaw"]
    else:
        cube_pos = cube_info["pos"]
        cube_yaw = cube_info["yaw"]
    
    # Desired grasp height: tool point at cube centre (z of cube centre)
    grasp_z = cube_pos[2]          # centre of cube on table
    # Safety offset above the cube for approach
    approach_z = grasp_z + 0.08    # 8 cm above centre
    
    # Approach position (above the cube)
    above_pos = [cube_pos[0], cube_pos[1], approach_z]
    
    # Number of grasp attempts
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Move to above the cube (fast)
            robot.move_to(above_pos[0], above_pos[1], above_pos[2], speed=0.2)
            # Descend to grasp height (slow)
            robot.move_to(cube_pos[0], cube_pos[1], grasp_z, yaw=cube_yaw, speed=0.05)
        except Exception as e:
            robot.log(f"Move error on attempt {attempt}: {e}")
            # Retry after lifting a bit
            robot.move_by(dz=0.02, speed=0.1)
            continue
        
        # Try to grasp
        if robot.grasp():
            # Verify we are holding something
            if robot.holding() == "red_cube":
                robot.log(f"Grasp successful on attempt {attempt}")
                break
            else:
                robot.log("Grasp returned True but not holding red_cube")
                robot.release()
        else:
            robot.log(f"Grasp failed on attempt {attempt}")
            robot.release()
        
        # If grasp failed, retreat a little and try again
        robot.move_by(dz=0.02, speed=0.1)
    else:
        # All attempts exhausted
        robot.log("Failed to grasp red cube after multiple attempts")
        return False
    
    # Lift the cube at least 5 cm above the table
    # Current tool point is at grasp_z; raise by 0.05 m + a small margin
    lift_target_z = grasp_z + 0.06  # 6 cm above centre => ~5 cm above tabletop
    try:
        robot.move_to(cube_pos[0], cube_pos[1], lift_target_z, yaw=cube_yaw, speed=0.1)
    except Exception as e:
        robot.log(f"Lift error: {e}")
        # Still consider success if we are holding and already high enough?
        # Check current height
        cur_pos = robot.observe()["gripper"]["pos"]
        if cur_pos[2] >= 0.05 and robot.holding() == "red_cube":
            return True
        return False
    
    # Final verification: check height and holding status
    final_obs = robot.observe()
    gripper_pos = final_obs["gripper"]["pos"]
    holding = robot.holding()
    success = (holding == "red_cube") and (gripper_pos[2] >= 0.05)
    robot.log(f"Final check: holding={holding}, gripper_z={gripper_pos[3]:.3f}" if False else f"Final check: holding={holding}, gripper_z={gripper_pos[2]:.3f}")
    return success
