import math

def run(robot):
    # Home to start cleanly
    robot.home()
    
    # Get latest perception
    obs = robot.observe()
    red_pose = obs["objects"]["red_cube"]
    blue_pose = obs["objects"]["blue_cube"]
    
    red_pos = red_pose["pos"]
    blue_pos = blue_pose["pos"]
    red_yaw = red_pose["yaw"]
    blue_yaw = blue_pose["yaw"]
    
    CUBE_SIZE = 0.03          # side length
    HALF = CUBE_SIZE / 2.0    # 0.015
    GRASP_Z = HALF            # tool point height for grasping (finger pads around middle)
    ABOVE_Z = 0.08            # safe height to approach/release
    
    # Helper to move with a given speed
    def move(x, y, z, yaw=None, speed=0.15):
        try:
            return robot.move_to(x, y, z, yaw=yaw, speed=speed)
        except Exception as e:
            robot.log("MotionError:", e)
            return {"ok": False}
    
    # 1. Move above red cube
    move(red_pos[0], red_pos[1], ABOVE_Z, yaw=red_yaw, speed=0.15)
    # 2. Lower to grasp height
    move(red_pos[0], red_pos[1], GRASP_Z, yaw=red_yaw, speed=0.05)
    # 3. Attempt grasp
    if not robot.grasp():
        robot.log("Grasp failed on red cube")
        robot.home()
        return False
    # Verify hold
    if robot.holding() != "red_cube":
        robot.log("Not holding red cube after grasp")
        robot.release()
        robot.home()
        return False
    
    # 4. Lift red cube
    move(red_pos[0], red_pos[1], ABOVE_Z, yaw=red_yaw, speed=0.05)
    
    # 5. Move above blue cube
    move(blue_pos[0], blue_pos[1], ABOVE_Z, yaw=blue_yaw, speed=0.15)
    # 6. Lower to stacking height (blue cube top)
    stack_z = blue_pos[2] + CUBE_SIZE  # center of red cube when stacked
    move(blue_pos[0], blue_pos[1], stack_z, yaw=blue_yaw, speed=0.05)
    # 7. Release
    robot.release()
    # Verify release
    if robot.holding() is not None:
        robot.log("Still holding after release")
        robot.home()
        return False
    
    # 8. Retreat
    move(blue_pos[0], blue_pos[1], ABOVE_Z, yaw=blue_yaw, speed=0.05)
    robot.home()
    return True
