import math

def run(robot):
    max_attempts = 3
    safe_x_min, safe_x_max = 0.06, 0.30
    safe_y_min, safe_y_max = -0.24, 0.24
    approach_z = 0.0225
    push_z = 0.0225
    retract_x, retract_y, retract_z = 0.15, 0.0, 0.15
    approach_margin = 0.03
    min_push_distance = 0.02

    def clamp_point(x, y):
        """Clamp to the safe rectangle (2 cm inside hard limits)."""
        x = max(safe_x_min, min(safe_x_max, x))
        y = max(safe_y_min, min(safe_y_max, y))
        return x, y

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

        if dist <= target_radius:
            robot.log("Puck already inside target")
            return True

        if dist < 1e-3:
            robot.log("Puck and target centres coincide")
            return True

        ux = dx / dist
        uy = dy / dist

        # Approach point: behind the puck (further from target)
        approach_dist = puck_radius + approach_margin
        approach_x = puck_pos[0] - ux * approach_dist
        approach_y = puck_pos[1] - uy * approach_dist

        # Push point: target centre minus puck_radius (so puck centre ends at target)
        push_x = target_pos[0] - ux * puck_radius
        push_y = target_pos[1] - uy * puck_radius

        # Clamp both points to safe rectangle
        approach_x, approach_y = clamp_point(approach_x, approach_y)
        push_x, push_y = clamp_point(push_x, push_y)

        # Ensure minimum push distance by moving approach further back if needed
        push_dx = push_x - approach_x
        push_dy = push_y - approach_y
        push_dist = math.hypot(push_dx, push_dy)
        if push_dist < min_push_distance:
            # Increase approach distance and recompute approach point
            extra = min_push_distance - push_dist + 0.005  # small buffer
            approach_dist += extra
            approach_x = puck_pos[0] - ux * approach_dist
            approach_y = puck_pos[1] - uy * approach_dist
            approach_x, approach_y = clamp_point(approach_x, approach_y)
            push_dx = push_x - approach_x
            push_dy = push_y - approach_y
            push_dist = math.hypot(push_dx, push_dy)
            if push_dist < 0.005:
                robot.log("Push distance still too small after adjustment")
                robot.wait(0.5)
                continue

        # Yaw aligned with the original puck→target direction
        push_yaw = math.atan2(uy, ux)

        try:
            # Move to approach position (high then low)
            robot.move_to(approach_x, approach_y, 0.15, speed=0.15)
            robot.move_to(approach_x, approach_y, approach_z, speed=0.05)

            # Push forward slowly
            robot.move_to(push_x, push_y, push_z, yaw=push_yaw, speed=0.03)

            # Brief pause to let puck settle
            robot.wait(0.2)

            # Retract to fixed safe zone for clear view
            robot.move_to(retract_x, retract_y, retract_z, speed=0.15)
            robot.wait(0.3)

        except Exception as e:
            robot.log(f"Motion error on attempt {attempt}: {e}")
            # Recover to safe height
            try:
                robot.move_to(retract_x, retract_y, retract_z, speed=0.15)
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
            # Otherwise loop retries with updated positions
        else:
            robot.log("Puck not visible after push")

    robot.log("All attempts failed")
    return False
