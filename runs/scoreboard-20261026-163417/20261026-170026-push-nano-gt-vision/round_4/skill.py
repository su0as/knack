# skill module
import math
import numpy as np

def run(robot):
    """
    Push the orange puck so that its centre ends up inside the green circular zone.
    Works for any random layout by perceiving the scene at runtime.
    Returns True if the puck finishes inside the zone, otherwise False.
    """
    # ---------- 1. Perceive ----------
    try:
        obs = robot.observe()
    except Exception as e:
        robot.log("observe failed:", e)
        return False

    objs = obs.get("objects", {})
    fixtures = obs.get("fixtures", {})

    # locate puck and target zone
    puck_name = None
    target_name = None
    for name, data in objs.items():
        if data.get("color") == "orange" and data.get("shape") == "puck":
            puck_name = name
    for name, data in fixtures.items():
        if data.get("color") == "green" and "radius" in data:
            target_name = name

    if not puck_name or not target_name:
        robot.log("could not find puck or target zone")
        return False

    puck = objs[puck_name]
    target = fixtures[target_name]

    puck_pos = np.array(puck["pos"])
    target_pos = np.array(target["pos"])
    target_radius = target["radius"]

    # ---------- 2. Compute push direction ----------
    push_dir = target_pos - puck_pos
    push_dist_norm = np.linalg.norm(push_dir)
    if push_dist_norm < 1e-3:
        robot.log("puck already at target centre")
        return True
    push_dir_u = push_dir / push_dist_norm

    # ---------- 3. Estimate puck radius ----------
    try:
        puck_radius = puck["size"]["radius"]
    except Exception:
        try:
            puck_radius = max(puck["size"]) / 2.0
        except Exception:
            puck_radius = 0.03  # safe default ~3 cm

    # ---------- 4. Plan contact pose ----------
    contact_offset = 0.05  # larger offset to stay clear of fixtures/edges
    contact_pos = puck_pos - push_dir_u * (puck_radius + contact_offset)

    # safety clamp (original limits)
    def clamp_pose(x, y, z):
        x = max(0.04, min(0.32, x))
        y = max(-0.26, min(0.26, y))
        z = max(0.014, min(0.26, z))
        return x, y, z

    cx, cy, cz = clamp_pose(*contact_pos)

    # ---------- 5. Move to contact pose (with single fallback) ----------
    def try_move_to(x, y, z, speed=0.07):
        try:
            return robot.move_to(x, y, z, speed=speed)
        except Exception as e:
            robot.log("move_to failed:", e)
            # try a slightly lower target once
            return try_move_to(x, y, z - 0.002, speed=speed)

    try:
        move_res = try_move_to(cx, cy, cz, speed=0.07)
        if not move_res["ok"]:
            robot.log("move_to contact still blocked after retry")
            return False
    except Exception as e:
        robot.log("move_to contact ultimately failed:", e)
        return False

    # ---------- 6. Close fingers to make contact ----------
    # Two grasp attempts: first at full height, second after a tiny drop
    if not robot.grasp():
        robot.log("grasp returned False – first attempt")
        try:
            robot.move_to(cx, cy, cz - 0.004, speed=0.07)  # extra drop for stable contact
            if not robot.grasp():
                robot.log("grasp failed again after height drop")
                return False
        except Exception as e:
            robot.log("grasp retry motion failed:", e)
            return False

    # ---------- 7. Push towards the target ----------
    # Scale down displacement to compensate for slip (empirically 0.7)
    push_scale = 0.7
    dx = push_dir_u[0] * push_dist_norm * push_scale
    dy = push_dir_u[1] * push_dist_norm * push_scale

    try:
        robot.move_by(dx=dx, dy=dy, speed=0.07)
    except Exception as e:
        robot.log("first push move failed:", e)
        # fallback: smaller push (half of scaled distance)
        try:
            robot.move_by(dx=dx * 0.5, dy=dy * 0.5, speed=0.07)
        except Exception:
            pass  # give up on this episode

    # If after the first push the puck is still outside, try a second tiny push
    # (only if we have not yet succeeded)
    try:
        final_pos = np.array(robot.get_pose(puck_name)["pos"])
        if np.linalg.norm(final_pos - target_pos) > target_radius:
            # second small push in the same direction
            robot.move_by(dx=dx * 0.3, dy=dy * 0.3, speed=0.07)
    except Exception:
        pass  # ignore if pose unavailable

    # ---------- 8. Release the puck ----------
    robot.release()

    # ---------- 9. Verify success ----------
    try:
        final_pos = np.array(robot.get_pose(puck_name)["pos"])
    except Exception:
        robot.log("could not get final puck pose")
        return False

    dist_to_target = np.linalg.norm(final_pos - target_pos)
    if dist_to_target <= target_radius:
        robot.log("puck successfully inside green zone")
        return True

    # ---------- 10. Optional single retry with jitter ----------
    try:
        jitter = np.array([0.005, 0.0, 0.0])  # deterministic +/-5 mm in x
        retry_contact = contact_pos + jitter
        rx, ry, rz = clamp_pose(*retry_contact)

        robot.move_to(rx, ry, rz, speed=0.07)
        if robot.grasp():
            robot.move_by(dx=dx, dy=dy, speed=0.07)
            robot.release()
            # final check after retry
            final_pos2 = np.array(robot.get_pose(puck_name)["pos"])
            if np.linalg.norm(final_pos2 - target_pos) <= target_radius:
                robot.log("puck inside zone on retry")
                return True
    except Exception as e:
        robot.log("retry failed:", e)

    robot.log("puck not inside zone after push, distance:", dist_to_target)
    return False
