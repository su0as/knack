import math

def run(robot):
    """Push the orange puck until its centre lies inside the green zone."""
    MAX_ATTEMPTS = 3
    APPROACH_Z = 0.08      # safe height for approach/retreat
    PUSH_Z = 0.02          # just above table to make contact
    BACK_OFFSET = 0.06     # distance behind puck to start push
    OVERSHOOT = 0.02       # extra travel beyond the needed distance (restored)

    for attempt in range(MAX_ATTEMPTS):
        # -------------------------------------------------
        # 1. Perceive the scene
        # -------------------------------------------------
        try:
            obs = robot.observe()
        except Exception as e:
            robot.log("observe failed:", e)
            robot.home()
            continue

        if "puck" not in obs["objects"]:
            robot.log("puck not visible, homing and retrying")
            robot.home()
            continue

        puck = obs["objects"]["puck"]
        target = obs["fixtures"]["target"]

        puck_pos = puck["pos"]
        target_pos = target["pos"]

        # -------------------------------------------------
        # 2. Check if already inside target
        # -------------------------------------------------
        dx = target_pos[0] - puck_pos[0]
        dy = target_pos[1] - puck_pos[1]
        dist_to_target = math.hypot(dx, dy)
        if dist_to_target <= target["radius"] - 0.005:  # small margin
            robot.log("puck already in target")
            return True

        # -------------------------------------------------
        # 3. Compute push direction and start point
        # -------------------------------------------------
        if dist_to_target < 1e-6:  # avoid division by zero
            robot.log("puck and target coincident but not inside?")
            return False

        ux = dx / dist_to_target
        uy = dy / dist_to_target

        start_x = puck_pos[0] - ux * BACK_OFFSET
        start_y = puck_pos[1] - uy * BACK_OFFSET

        # Clamp to wider workspace limits to avoid edge collisions
        start_x = max(0.02, min(0.34, start_x))
        start_y = max(-0.28, min(0.28, start_y))

        end_x = start_x + ux * (dist_to_target + OVERSHOOT)
        end_y = start_y + uy * (dist_to_target + OVERSHOOT)
        # Also widen end point clamping for consistency
        end_x = max(0.02, min(0.34, end_x))
        end_y = max(-0.28, min(0.28, end_y))

        # -------------------------------------------------
        # 4. Execute the push motion
        # -------------------------------------------------
        try:
            # Move to start point above the table
            robot.move_to(start_x, start_y, APPROACH_Z, speed=0.15)
            # Lower to pushing height
            robot.move_to(start_x, start_y, PUSH_Z, speed=0.05)
            # Push forward
            robot.move_to(end_x, end_y, PUSH_Z, speed=0.05)
            # Retract to safe height
            robot.move_to(end_x, end_y, APPROACH_Z, speed=0.15)
            # Small backward retreat to keep puck in view
            robot.move_to(end_x, end_y - 0.02, APPROACH_Z, speed=0.15)
        except Exception as e:
            robot.log("motion error:", e)
            # If something went wrong, go home and try again
            robot.home()
            continue

        # -------------------------------------------------
        # 5. Verify result
        # -------------------------------------------------
        try:
            obs2 = robot.observe()
        except Exception as e:
            robot.log("post-push observe failed:", e)
            robot.home()
            continue

        if "puck" not in obs2["objects"]:
            robot.log("puck lost after push")
            robot.home()
            continue

        puck2 = obs2["objects"]["puck"]
        px, py = puck2["pos"][0], puck2["pos"][1]
        tx, ty = target_pos[0], target_pos[1]
        final_dist = math.hypot(px - tx, py - ty)

        robot.log(
            f"attempt {attempt+1}: puck at ({px:.3f},{py:.3f}), "
            f"target at ({tx:.3f},{ty:.3f}), dist={final_dist:.3f}"
        )

        if final_dist <= target["radius"] - 0.005:
            return True

    # Exhausted attempts
    robot.log("failed to push puck into target after", MAX_ATTEMPTS, "attempts")
    return False
