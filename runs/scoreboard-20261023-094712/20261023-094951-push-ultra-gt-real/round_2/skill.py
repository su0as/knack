import math
import numpy as np

def run(robot):
    # Workspace bounds
    X_MIN, X_MAX = 0.04, 0.32
    Y_MIN, Y_MAX = -0.26, 0.26
    
    def clamp_xy(x, y):
        return (max(X_MIN, min(X_MAX, x)), max(Y_MIN, min(Y_MAX, y)))
    
    def rotate_vec(v, angle):
        ca, sa = math.cos(angle), math.sin(angle)
        return np.array([ca * v[0] - sa * v[1], sa * v[0] + ca * v[1]])
    
    max_attempts = 8
    push_z = 0.02          # tool-point height: finger pads ~0.0075, puck centre ~0.01
    approach_base = 0.05   # 2 cm behind puck edge (radius 0.03 + 0.02)
    
    for attempt in range(max_attempts):
        obs = robot.observe()
        puck = obs["objects"]["puck"]
        target = obs["fixtures"]["target"]
        
        puck_pos = np.array(puck["pos"])
        target_pos = np.array(target["pos"])
        target_radius = target["radius"]
        puck_radius = puck["size"]["radius"]
        
        # Vector from puck to target (XY only)
        to_target = target_pos[:2] - puck_pos[:2]
        dist_to_target = np.linalg.norm(to_target)
        
        if dist_to_target <= target_radius + 1e-3:
            robot.log(f"Success: puck in target, dist={dist_to_target:.4f}")
            return True
        
        # Base push direction
        push_dir = to_target / dist_to_target
        
        # Lead angle to counteract sideways slide of upright puck
        lead_angle = puck_radius / max(dist_to_target, 0.01)
        push_dir = rotate_vec(push_dir, lead_angle)
        
        # Check puck orientation: yaw in [-pi/4, pi/4), 0 = faces aligned with world axes
        # Edge-on when |yaw| ~ pi/4. Dot product with push_dir indicates face-on vs edge-on.
        puck_yaw = puck["yaw"]
        puck_forward = np.array([math.cos(puck_yaw), math.sin(puck_yaw)])
        face_on = abs(np.dot(puck_forward, push_dir))
        
        # If edge-on (face_on < 0.5), increase approach distance and raise push_z slightly
        approach_dist = approach_base
        local_push_z = push_z
        if face_on < 0.5:
            approach_dist += 0.02
            local_push_z += 0.01
        
        # Start position behind puck
        start_xy = puck_pos[:2] - push_dir * approach_dist
        start_xy = clamp_xy(start_xy[0], start_xy[1])
        
        # End position: push past target by puck_radius + margin
        push_distance = dist_to_target + puck_radius + 0.02
        end_xy = puck_pos[:2] + push_dir * push_distance
        end_xy = clamp_xy(end_xy[0], end_xy[1])
        
        # Move to start: above first, then down
        try:
            robot.move_to(start_xy[0], start_xy[1], 0.10, speed=0.15)
            robot.move_to(start_xy[0], start_xy[1], local_push_z, speed=0.05)
        except Exception as e:
            robot.log(f"Move to start failed: {e}")
            continue
        
        # Push forward
        try:
            robot.move_to(end_xy[0], end_xy[1], local_push_z, speed=0.05)
        except Exception as e:
            robot.log(f"Push move failed: {e}")
            continue
        
        robot.wait(0.2)  # let physics settle
    
    # Final check after attempts
    obs = robot.observe()
    puck = obs["objects"]["puck"]
    target = obs["fixtures"]["target"]
    puck_pos = np.array(puck["pos"])
    target_pos = np.array(target["pos"])
    target_radius = target["radius"]
    dist = np.linalg.norm(target_pos[:2] - puck_pos[:2])
    robot.log(f"Final dist to target: {dist:.4f}, target radius: {target_radius:.4f}")
    return dist <= target_radius
