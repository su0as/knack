import math

def run(robot):
    # Observe initial scene
    obs = robot.observe()
    puck = obs["objects"]["puck"]
    target = obs["fixtures"]["target"]
    
    puck_pos = puck["pos"]
    target_pos = target["pos"]
    puck_radius = puck["size"]["radius"]
    puck_height = puck["size"]["height"]
    
    # Calculate push direction: from puck to target
    dx = target_pos[0] - puck_pos[0]
    dy = target_pos[1] - puck_pos[1]
    push_dist = math.hypot(dx, dy)
    if push_dist < 1e-3:
        return True  # already there
    
    # Unit vector in push direction
    ux = dx / push_dist
    uy = dy / push_dist
    
    # Yaw for gripper: fingers close along perpendicular to push direction
    push_yaw = math.atan2(uy, ux)
    gripper_yaw = push_yaw + math.pi/2
    
    # Start position: behind puck by 10cm + puck radius (increased from 5cm)
    start_offset = 0.10 + puck_radius
    start_x = puck_pos[0] - ux * start_offset
    start_y = puck_pos[1] - uy * start_offset
    
    # Tool point height: finger pads are 0.0125 m below tool point.
    # We want finger pads at puck center height (puck_pos[2]) for good contact.
    # Also ensure tool point clears puck top by a small margin.
    puck_top = puck_pos[2] + puck_height / 2.0
    start_z = max(puck_pos[2] + 0.0125, puck_top + 0.005)
    # Safety floor
    if start_z < 0.014:
        start_z = 0.014
    robot.log(f"Start_z set to {start_z:.4f} m (puck_center={puck_pos[2]:.4f}, puck_top={puck_top:.4f})")
    
    # Validate horizontal clearance (should be satisfied with new offset)
    required_clearance = puck_radius + 0.02
    current_clearance = math.hypot(start_x - puck_pos[0], start_y - puck_pos[1])
    if current_clearance < required_clearance:
        shift = required_clearance - current_clearance
        start_x -= ux * shift
        start_y -= uy * shift
        robot.log(f"Adjusted start position by {shift:.4f} m for horizontal clearance")
    
    # Move to start position
    try:
        robot.move_to(start_x, start_y, start_z, yaw=gripper_yaw, speed=0.1)
    except Exception as e:
        robot.log("Move to start failed:", e)
        return False
    
    # Push forward: move in push direction by push_dist + adaptive margin
    margin = max(0.03, target["radius"] * 1.5)
    push_length = push_dist + margin
    end_x = start_x + ux * push_length
    end_y = start_y + uy * push_length
    
    robot.log(f"Push dist: {push_dist:.4f}, margin: {margin:.4f}, push_length: {push_length:.4f}")
    
    # Move slowly to push
    try:
        robot.move_to(end_x, end_y, start_z, yaw=gripper_yaw, speed=0.05)
    except Exception as e:
        robot.log("Push move failed:", e)
        return False
    
    # Reverse tap to dampen overshoot
    try:
        robot.move_by(dx=-ux*0.04, dy=-uy*0.04, speed=0.05)
    except Exception as e:
        robot.log("Reverse tap failed:", e)
        # continue anyway
    
    # Verify puck position
    obs2 = robot.observe()
    puck2 = obs2["objects"]["puck"]
    puck2_pos = puck2["pos"]
    dist_to_target = math.hypot(puck2_pos[0] - target_pos[0], puck2_pos[1] - target_pos[1])
    
    robot.log(f"Puck final dist to target: {dist_to_target:.4f}, target radius: {target['radius']:.4f}")
    return dist_to_target <= target["radius"]
