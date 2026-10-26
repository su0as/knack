import math

def run(robot):
    max_attempts = 2
    for attempt in range(max_attempts):
        obs = robot.observe()
        puck = obs['objects'].get('puck')
        target = obs['fixtures'].get('target')
        if not puck or not target:
            robot.log("Missing puck or target")
            return False

        puck_pos = puck['pos']
        target_pos = target['pos']
        target_radius = target['radius']
        puck_radius = puck['size']['radius']

        # Vector from puck to target centre
        dx = target_pos[0] - puck_pos[0]
        dy = target_pos[1] - puck_pos[1]
        dist = math.hypot(dx, dy)

        if dist < 1e-3:
            robot.log("Puck already at target")
            return True

        ux = dx / dist
        uy = dy / dist

        # Approach position: behind the puck
        approach_dist = 2 * puck_radius + 0.05
        approach_x = puck_pos[0] - ux * approach_dist
        approach_y = puck_pos[1] - uy * approach_dist
        approach_z = 0.0225  # tool‑point height for mid‑puck push

        # Push target: just beyond the target centre
        push_margin = puck_radius + 0.02
        push_x = target_pos[0] + ux * push_margin
        push_y = target_pos[1] + uy * push_margin
        push_z = approach_z

        # Safe workspace limits (with 2 cm margin from hard limits)
        safe_x_min, safe_x_max = 0.06, 0.30
        safe_y_min, safe_y_max = -0.24, 0.24
        max_reach = 0.24  # max horizontal distance from base at table height

        def clamp_point(x, y):
            # Clamp to rectangle
            x = max(safe_x_min, min(safe_x_max, x))
            y = max(safe_y_min, min(safe_y_max, y))
            # Clamp to reachability circle
            d = math.hypot(x, y)
            if d > max_reach:
                scale = max_reach / d
                x *= scale
                y *= scale
            return x, y

        approach_x, approach_y = clamp_point(approach_x, approach_y)
        push_x, push_y = clamp_point(push_x, push_y)

        # Yaw aligned with push direction (fingers close along push axis)
        push_yaw = math.atan2(uy, ux)

        try:
            # Move to approach position (high then low)
            robot.move_to(approach_x, approach_y, 0.15, speed=0.15)
            robot.move_to(approach_x, approach_y, approach_z, speed=0.05)

            # Push forward slowly
            robot.move_to(push_x, push_y, push_z, yaw=push_yaw, speed=0.03)

            # Brief pause to let puck settle
            robot.wait(0.2)

            # Retract to clear view
            robot.move_to(approach_x, approach_y, 0.15, speed=0.15)
            robot.wait(0.3)

        except Exception as e:
            robot.log(f"Motion error on attempt {attempt}: {e}")
            # Try to recover to safe height
            try:
                robot.move_to(approach_x, approach_y, 0.15, speed=0.15)
            except Exception:
                pass
            continue

        # Verify
        obs2 = robot.observe()
        puck2 = obs2['objects'].get('puck')
        if puck2:
            px, py, _ = puck2['pos']
            tx, ty, _ = target_pos
            final_dist = math.hypot(px - tx, py - ty)
            robot.log(f"Attempt {attempt}: final puck-target distance: {final_dist:.4f}, target radius: {target_radius}")
            if final_dist <= target_radius:
                return True
            # If not within tolerance, loop will retry with updated positions
        else:
            robot.log("Puck not visible after push")

    robot.log("All attempts failed")
    return False
