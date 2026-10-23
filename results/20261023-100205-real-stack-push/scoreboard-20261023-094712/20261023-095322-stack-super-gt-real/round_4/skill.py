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
    GRASP_Z = HALF + 0.005    # tool point height for grasping (slightly higher for clearance)
    ABOVE_Z = 0.08            # safe height to approach/release
    EPS = 0.001               # small clearance epsilon
    
    # Helper to move with a given speed, with basic retry on failure
    def safe_move(x, y, z, yaw=None, speed=0.15, max_tries=3):
        for _ in range(max_tries):
            try:
                res = robot.move_to(x, y, z, yaw=yaw, speed=speed)
                if res.get("ok", False):
                    return res
                robot.log("Move not ok:", res)
            except Exception as e:
                robot.log("MotionError:", e)
            robot.wait(0.1)  # brief pause before retry
        return {"ok": False}
    
    # 1. Move above red cube
    res = safe_move(red_pos[0], red_pos[1], ABOVE_Z, yaw=red_yaw, speed=0.15)
    if not res["ok"]:
        robot.log("Failed to move above red cube")
        robot.home()
        return False
    
    # 2. Lower to grasp height
    res = safe_move(red_pos[0], red_pos[1], GRASP_Z, yaw=red_yaw, speed=0.05)
    if not res["ok"]:
        robot.log("Failed to move to grasp height")
        robot.home()
        return False
    
    # 3. Re‑observe red cube to counteract any drift before grasping
    obs = robot.observe()
    red_pose = obs["objects"]["red_cube"]
    red_pos = red_pose["pos"]
    red_yaw = red_pose["yaw"]
    
    # 4. Attempt grasp
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
    
    # 5. Lift red cube to safe height
    res = safe_move(red_pos[0], red_pos[1], ABOVE_Z, yaw=red_yaw, speed=0.05)
    if not res["ok"]:
        robot.log("Failed to lift red cube")
        robot.release()
        robot.home()
        return False
    
    # 6. Re‑observe blue cube pose (it may have shifted)
    obs = robot.observe()
    blue_pose = obs["objects"]["blue_cube"]
    blue_pos = blue_pose["pos"]
    blue_yaw = blue_pose["yaw"]
    
    # 7. Move above blue cube
    res = safe_move(blue_pos[0], blue_pos[1], ABOVE_Z, yaw=blue_yaw, speed=0.15)
    if not res["ok"]:
        robot.log("Failed to move above blue cube")
        robot.release()
        robot.home()
        return False
    
    # 8. Lower to stacking height (red cube centre when stacked on blue)
    stack_z = blue_pos[2] + CUBE_SIZE + EPS  # centre height with tiny clearance
    res = safe_move(blue_pos[0], blue_pos[1], stack_z, yaw=blue_yaw, speed=0.05)
    if not res["ok"]:
        robot.log("Failed to lower to stack height")
        robot.release()
        robot.home()
        return False
    
    # Brief settle to let contacts stabilize
    robot.wait(0.2)
    
    # 9. Release
    robot.release()
    # Verify release
    if robot.holding() is not None:
        robot.log("Still holding after release")
        robot.home()
        return False
    
    # 10. Retreat
    res = safe_move(blue_pos[0], blue_pos[1], ABOVE_Z, yaw=blue_yaw, speed=0.05)
    if not res["ok"]:
        robot.log("Failed to retreat")
        robot.home()
        return False
    
    robot.home()
    return True
