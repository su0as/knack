# skill module
import math
import numpy as np

def run(robot):
    """
    Push the orange puck so that its centre ends up inside the green circular zone.
    The skill works for any random layout by perceiving the scene at runtime.
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

    # ---------- 3. Plan contact pose ----------
    # puck radius: assume it is stored as a scalar radius in size dict,
    # fallback to half of the first size dimension if missing
    try:
        puck_radius = puck["size"]["radius"]
    except Exception:
        # size may be a list like [dx, dy, dz]; take max dimension / 2
        try:
            puck_radius = max(puck["size"]) / 2.0
        except Exception:
            puck_radius = 0.03  # safe default ~3 cm

    contact_offset = 0.04  # larger offset to stay clear of the edge
    contact_pos = puck_pos - push_dir_u * (puck_radius + contact_offset)

    # safety clamp (now allows z up to 0.28)
    def clamp_pose(x, y, z):
        x = max(0.04, min(0.32, x))
        y = max(-0.26, min(0.26, y))
        z = max(0.014, min(0.28, z))  # ceiling raised to 0.28
        return x, y, z

    cx, cy, cz = clamp_pose(*contact_pos)

    # ---------- 4. Move to contact pose (with fallback) ----------
    def try_move_to(x, y, z, speed=0.07):
        try:
            return robot.move_to(x, y, z, speed=speed)
        except Exception as e:  # MotionError or any other
            robot.log("move_to failed:", e)
            # attempt a softer, slightly lower target once
            return try_move_to(x, y, z - 0.005, speed=speed)

    try:
        move_res = try_move_to(cx, cy, cz, speed=0.07)
        if not move_res["ok"]:
            robot.log("move_to contact still blocked after retry")
            return False
    except Exception as e:
        robot.log("move_to contact ultimately failed:", e)
        return False

    # ---------- 5. Close fingers to make contact ----------
    if not robot.grasp():
        robot.log("grasp returned False – no contact made")
        # try a modest height reduction and grasp again
        try:
            robot.move_to(cx, cy, cz * 0.95, speed=0.07)
            if not robot.grasp():
                return False
        except Exception:
            return False

    # ---------- 6. Push towards the target ----------
    push_distance = 0.95 * push_dist_norm  # more aggressive fraction
    dx = push_dir_u[0] * push_distance
    dy = push_dir_u[1] * push_distance
    try:
        robot.move_by(dx=dx, dy=dy, speed=0.07)
    except Exception as e:
        robot.log("first push move failed:", e)
        # fallback: smaller push
        try:
            robot.move_by(dx=dx * 0.5, dy=dy * 0.5, speed=0.07)
        except Exception:
            pass  # give up on this episode

    # ---------- 7. Release the puck ----------
    robot.release()

    # ---------- 8. Verify success ----------
    try:
        final_pos = np.array(robot.get_pose(puck_name)["pos"])
    except Exception:
        robot.log("could not get final puck pose")
        return False

    dist_to_target = np.linalg.norm(final_pos - target_pos)
    if dist_to_target <= target_radius:
        robot.log("puck successfully inside green zone")
        return True

    # ---------- 9. Optional single retry with jitter ----------
    try:
        # small deterministic jitter to change approach angle
        jitter = np.array([0.005, 0.0, 0.0])  # +/-5 mm in x
        retry_contact = contact_pos + jitter
        rx, ry, rz = clamp_pose(*retry_contact)

        # repeat move‑to, grasp, push (same distance)
        robot.move_to(rx, ry, rz, speed=0.07)
        if robot.grasp():
            robot.move_by(dx=dx, dy=dy, speed=0.07)
            robot.release()
            # final check
            final_pos2 = np.array(robot.get_pose(puck_name)["pos"])
            if np.linalg.norm(final_pos2 - target_pos) <= target_radius:
                robot.log("puck inside zone on retry")
                return True
    except Exception as e:
        robot.log("retry failed:", e)

    robot.log("puck not inside zone after push, distance:", dist_to_target)
    return False
