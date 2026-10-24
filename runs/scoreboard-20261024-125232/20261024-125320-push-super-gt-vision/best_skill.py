import math

def run(robot):
    """Push the puck into the target zone."""
    # Helper to get pose safely, returning None if missing
    def safe_get_pose(name):
        try:
            return robot.get_pose(name)
        except LookupError:
            return None

    # 1. Observe scene
    obs = robot.observe()
    puck_info = obs.get("objects", {}).get("puck")
    target_info = obs.get("fixtures", {}).get("target")
    if not puck_info or not target_info:
        robot.log("Missing puck or target in observation")
        return False

    puck_pos = puck_info["pos"]
    target_pos = target_info["pos"]
    puck_radius = puck_info["size"]["radius"]  # 0.03 m

    # 2. Compute push direction (from puck to target)
    dx = target_pos[0] - puck_pos[0]
    dy = target_pos[1] - puck_pos[1]
    dist_xy = math.hypot(dx, dy)
    if dist_xy < 1e-6:
        robot.log("Puck already at target centre")
        # Still check if inside zone
        inside = dist_xy <= target_info["radius"]
        return inside
    ux, uy = dx / dist_xy, dy / dist_xy  # unit vector toward target

    # 3. Choose a point behind the puck to start pushing
    # Offset behind puck by puck_radius + a small clearance (reduced to minimise pose error)
    offset = puck_radius + 0.005  # 0.5 cm clearance
    push_start = [
        puck_pos[0] - ux * offset,
        puck_pos[1] - uy * offset,
        puck_pos[2]  # keep same height as puck centre
    ]

    # 4. Define pushing height (tool point height)
    # Fingertips are 1.25 cm below tool point; we want them just above the puck's equator.
    push_z = 0.02  # a bit above table, will contact side of puck

    try:
        # Move to a safe clearance above the push start (increased clearance)
        robot.move_to(push_start[0], push_start[1], push_start[2] + 0.15, speed=0.2)
        # Lower to pushing height
        robot.move_to(push_start[0], push_start[1], push_z, speed=0.05)
        # Push forward along the direction for a distance (increased push distance)
        push_distance = 0.12  # 12 cm push
        push_end = [
            push_start[0] + ux * push_distance,
            push_start[1] + uy * push_distance,
            push_z
        ]
        robot.move_to(push_end[0], push_end[1], push_end[2], speed=0.05)
    except Exception as e:  # MotionError or other
        robot.log(f"Motion error during push: {e}")
        # Retreat to home and fail
        robot.home()
        return False

    # 5. Retract slightly to avoid dragging puck back
    # Move forward along push direction and lift up
    retract = [
        push_end[0] + ux * 0.02,
        push_end[1] + uy * 0.02,
        push_end[2] + 0.05
    ]
    try:
        robot.move_to(retract[0], retract[1], retract[2], speed=0.05)
    except Exception:
        pass  # best effort

    # 6. Home the robot
    robot.home()

    # 7. Verify result: re‑observe and check if puck inside target zone
    obs2 = robot.observe()
    puck2 = obs2.get("objects", {}).get("puck")
    if not puck2:
        robot.log("Puck disappeared after push")
        return False
    final_pos = puck2["pos"]
    dx_f = final_pos[0] - target_pos[0]
    dy_f = final_pos[1] - target_pos[1]
    dist_final = math.hypot(dx_f, dy_f)
    inside = dist_final <= target_info["radius"]
    robot.log(f"Final puck offset: ({dx_f:.4f}, {dy_f:.4f}) m, inside={inside}")
    return inside
