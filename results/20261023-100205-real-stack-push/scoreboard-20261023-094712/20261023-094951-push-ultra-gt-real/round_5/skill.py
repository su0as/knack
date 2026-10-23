import math
import numpy as np

def run(robot):
    # Workspace bounds (safety layer)
    X_MIN, X_MAX = 0.04, 0.32
    Y_MIN, Y_MAX = -0.26, 0.26
    
    def clamp_xy(x, y):
        return (max(X_MIN, min(X_MAX, x)), max(Y_MIN, min(Y_MAX, y)))
    
    def rotate_vec(v, angle):
        ca, sa = math.cos(angle), math.sin(angle)
        return np.array([ca * v[0] - sa * v[1], sa * v[0] + ca * v[1]])
    
    def ensure_clearance(xy, margin=0.05):
        """Shift xy away from walls if closer than margin."""
        x, y = xy
        shifted = False
        if x - X_MIN < margin:
            x = X_MIN + margin
            shifted = True
        if X_MAX - x < margin:
            x = X_MAX - margin
            shifted = True
        if y - Y_MIN < margin:
            y = Y_MIN + margin
            shifted = True
        if Y_MAX - y < margin:
            y = Y_MAX - margin
            shifted = True
        return (x, y) if shifted else xy
    
    max_attempts = 4
    push_z = 0.02          # tool-point height: finger pads ~0.0075, puck centre ~0.01
    approach_dist = 0.05   # 2 cm behind puck edge (radius 0.03 + 0.02)
    
    for attempt in range(max_attempts):
        obs = robot.observe()
        puck = obs["objects"]["puck"]
        target = obs["fixtures"]["target"]
        
        puck_pos = np.array(puck["pos"])
        target_pos = np.array(target["pos"])
        target_radius = target["radius"]
        
        # Robust radius extraction: size may be dict or list; default to 0.03 m
        puck_size = puck.get("size", {})
        if isinstance(puck_size, dict):
            puck_radius = puck_size.get("radius", 0.03)
        elif isinstance(puck_size, (list, tuple)) and len(puck_size) > 0:
            puck_radius = puck_size[0]
        else:
            puck_radius = 0.03
        puck_yaw = puck.get("yaw", 0.0)
        
        # Vector from puck to target (XY only)
        to_target = target_pos[:2] - puck_pos[:2]
        dist_to_target = np.linalg.norm(to_target)
        
        if dist_to_target <= target_radius + 1e-3:
            robot.log(f"Success: puck in target, dist={dist_to_target:.4f}")
            return True
        
        # Base push direction
        push_dir = to_target / dist_to_target
        
        # Lead angle to counteract sideways slide of upright puck
        lead_angle = 0.8 * puck_radius / max(dist_to_target, 0.01)
        push_dir = rotate_vec(push_dir, lead_angle)
        
        # Check puck orientation: yaw in [-pi/4, pi/4), 0 = faces aligned with world axes
        # Edge-on when |yaw| ~ pi/4. Dot product with push_dir indicates face-on vs edge-on.
        puck_forward = np.array([math.cos(puck_yaw), math.sin(puck_yaw)])
        face_on = abs(np.dot(puck_forward, push_dir))
        
        # If edge-on (face_on < 0.5), increase approach distance and raise push_z slightly
        local_approach_dist = approach_dist
        local_push_z = push_z
        if face_on < 0.5:
            local_approach_dist += 0.02
            local_push_z += 0.01
        
        # If puck already close to target, start farther back to reduce impact
        if dist_to_target < 0.1:
            local_approach_dist = max(local_approach_dist, 0.08)
        
        # Start position behind puck
        start_xy = puck_pos[:2] - push_dir * local_approach_dist
        start_xy = ensure_clearance(start_xy, margin=0.05)
        start_xy = clamp_xy(start_xy[0], start_xy[1])
        
        # End position: push past target by puck_radius + margin
        push_distance = dist_to_target + puck_radius + 0.04
        end_xy = puck_pos[:2] + push_dir * push_distance
        end_xy = clamp_xy(end_xy[0], end_xy[1])
        
        # Move to start: above first, then down
        try:
            robot.move_to(start_xy[0], start_xy[1], 0.10, speed=0.15)
            robot.move_to(start_xy[0], start_xy[1], local_push_z, speed=0.05)
        except Exception as e:
            robot.log(f"Move to start failed: {e}")
            continue
        
        # Push forward with yaw aligned to push direction, slow speed to avoid jamming
        push_yaw = math.atan2(push_dir[1], push_dir[0])
        try:
            robot.move_to(end_xy[0], end_xy[1], local_push_z, yaw=push_yaw, speed=0.02)
        except Exception as e:
            robot.log(f"Push move failed: {e}")
            continue
        
        robot.wait(0.2)  # let physics settle
        
        # Re-observe and check success
        obs = robot.observe()
        puck = obs["objects"]["puck"]
        puck_pos = np.array(puck["pos"])
        to_target = target_pos[:2] - puck_pos[:2]
        dist_to_target = np.linalg.norm(to_target)
        if dist_to_target <= target_radius + 1e-3:
            robot.log(f"Success: puck in target, dist={dist_to_target:.4f}")
            return True
        else:
            robot.log(f"Attempt {attempt+1}: puck dist to target = {dist_to_target:.4f}")
    
    # Final check after attempts
    obs = robot.observe()
    puck = obs["objects"]["puck"]
    target = obs["fixtures"]["target"]
    puck_pos = np.array(puck["pos"])
    target_pos = np.array(target["pos"])
    target_radius = target["radius"]
    dist = np.linalg.norm(target_pos[:2] - puck_pos[:2])
    robot.log(f"Final dist to target: {dist:.4f}, target radius: {target_radius:.4f}")
    return dist <= target_radius + 1e-3
