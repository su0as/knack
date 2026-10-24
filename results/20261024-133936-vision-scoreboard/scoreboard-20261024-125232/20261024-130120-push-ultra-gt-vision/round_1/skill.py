import math

def run(robot):
    # Get initial poses
    obs = robot.observe()
    puck = obs["objects"]["puck"]
    target = obs["fixtures"]["target"]
    
    puck_pos = puck["pos"]
    target_pos = target["pos"]
    puck_radius = puck["size"]["radius"]
    target_radius = target["radius"]
    
    # Vector from puck to target
    dx = target_pos[0] - puck_pos[0]
    dy = target_pos[1] - puck_pos[1]
    dist = math.hypot(dx, dy)
    
    if dist < 1e-6:
        return True  # already there
    
    # Unit vector from puck to target
    ux, uy = dx / dist, dy / dist
    
    # Position behind puck: back up by puck_radius + clearance
    clearance = 0.02  # 2cm behind puck
    start_x = puck_pos[0] - ux * (puck_radius + clearance)
    start_y = puck_pos[1] - uy * (puck_radius + clearance)
    
    # Push through puck to target: go to target_pos + a bit beyond
    push_dist = dist + puck_radius + 0.02
    end_x = puck_pos[0] + ux * push_dist
    end_y = puck_pos[1] + uy * push_dist
    
    # Clamp to workspace bounds
    def clamp(v, lo, hi):
        return max(lo, min(hi, v))
    
    start_x = clamp(start_x, 0.04, 0.32)
    start_y = clamp(start_y, -0.26, 0.26)
    end_x = clamp(end_x, 0.04, 0.32)
    end_y = clamp(end_y, -0.26, 0.26)
    
    # Approach height: tool point at puck mid-height (~0.015)
    approach_z = 0.015
    
    # Move to start position behind puck
    try:
        robot.move_to(start_x, start_y, approach_z, speed=0.10)
    except Exception:
        # Try a bit higher if blocked
        robot.move_to(start_x, start_y, 0.05, speed=0.10)
    
    # Push forward slowly
    try:
        robot.move_to(end_x, end_y, approach_z, speed=0.05)
    except Exception:
        pass
    
    # Verify: re-observe and check if puck center inside target zone
    robot.wait(0.5)
    obs2 = robot.observe()
    if "puck" in obs2["objects"]:
        puck2 = obs2["objects"]["puck"]
        px, py = puck2["pos"][0], puck2["pos"][1]
        tx, ty = target_pos[0], target_pos[1]
        if math.hypot(px - tx, py - ty) <= target_radius:
            return True
    
    # If not succeeded, try one more push from current position
    # Move back behind puck again
    obs3 = robot.observe()
    if "puck" in obs3["objects"]:
        puck3 = obs3["objects"]["puck"]
        px, py = puck3["pos"][0], puck3["pos"][1]
        dx2 = target_pos[0] - px
        dy2 = target_pos[1] - py
        dist2 = math.hypot(dx2, dy2)
        if dist2 > 1e-6:
            ux2, uy2 = dx2 / dist2, dy2 / dist2
            start_x2 = clamp(px - ux2 * (puck_radius + clearance), 0.04, 0.32)
            start_y2 = clamp(py - uy2 * (puck_radius + clearance), -0.26, 0.26)
            end_x2 = clamp(px + ux2 * (dist2 + puck_radius + 0.02), 0.04, 0.32)
            end_y2 = clamp(py + uy2 * (dist2 + puck_radius + 0.02), -0.26, 0.26)
            try:
                robot.move_to(start_x2, start_y2, approach_z, speed=0.10)
                robot.move_to(end_x2, end_y2, approach_z, speed=0.05)
            except Exception:
                pass
    
    # Final check
    robot.wait(0.5)
    obs_final = robot.observe()
    if "puck" in obs_final["objects"]:
        puck_f = obs_final["objects"]["puck"]
        px, py = puck_f["pos"][0], puck_f["pos"][1]
        if math.hypot(px - target_pos[0], py - target_pos[1]) <= target_radius:
            return True
    
    return False
