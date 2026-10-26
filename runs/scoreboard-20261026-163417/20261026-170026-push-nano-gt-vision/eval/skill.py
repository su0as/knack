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
        if data.get("color") == "green" and data.get("radius") is not None:
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
    # direction from puck to target centre
    push_dir = target_pos - puck_pos
    push_dir_norm = np.linalg.norm(push_dir)
    if push_dir_norm < 1e-3:
        robot.log("puck already at target centre")
        return True

    # unit vector pointing where we want to push
    push_dir_u = push_dir / push_dir_norm

    # ---------- 3. Plan contact pose ----------
    # we approach from the opposite side of the push direction,
    # at a height just above the tabletop (z ≈ 0.14) and lower until
    # the tool point is ~0.015 m above the table (the puck centre is at z≈0.01)
    # so that the finger pads touch the side of the puck.
    contact_offset = 0.02  # extra offset to ensure contact
    contact_pos = puck_pos - push_dir_u * (puck["size"]["radius"] + contact_offset)

    # ensure contact_pos respects safety limits; clamp if necessary
    def clamp_pose(x, y, z):
        x = max(0.04, min(0.32, x))
        y = max(-0.26, min(0.26, y))
        z = max(0.014, min(0.26, z))
        return x, y, z

    cx, cy, cz = clamp_pose(*contact_pos)
    cz = max(cz, 0.014)  # keep at least the minimal safe height

    # ---------- 4. Move to contact pose ----------
    try:
        robot.move_to(cx, cy, cz, speed=0.07)
    except Exception as e:  # MotionError or any other
        robot.log("move_to contact failed:", e)
        return False

    # ---------- 5. Close fingers to make contact ----------
    if not robot.grasp():
        robot.log("grasp returned False – no contact made")
        # try a second attempt with a slightly different height
        try:
            robot.move_to(cx, cy, cz * 0.95, speed=0.07)
            if not robot.grasp():
                return False
        except Exception:
            return False

    # ---------- 6. Push towards the target ----------
    # Desired displacement: move the puck so its centre reaches the target centre.
    # Use 0.9 of the required distance to avoid overshoot.
    push_distance = 0.9 * push_dir_norm
    # Convert to relative move in x/y (dz stays 0)
    dx = push_dir_u[0] * push_distance
    dy = push_dir_u[1] * push_distance
    try:
        robot.move_by(dx=dx, dy=dy, speed=0.07)
    except Exception as e:
        robot.log("move_by push failed:", e)
        # try a safer smaller push
        robot.move_by(dx=dx*0.5, dy=dy*0.5, speed=0.07)

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
    else:
        robot.log("puck not inside zone after push, distance:", dist_to_target)
        # optional retry: reposition and push again (simple single retry)
        try:
            # re‑approach from a slightly different angle
            offset = np.array([0.005, 0.0, 0.0])  # small jitter
            retry_contact = contact_pos + offset
            retry_cx, retry_cy, retry_cz = clamp_pose(*retry_contact)
            robot.move_to(retry_cx, retry_cy, retry_cz, speed=0.07)
            if robot.grasp():
                robot.move_by(dx=dx, dy=dy, speed=0.07)
                robot.release()
                # re‑check
                final_pos = np.array(robot.get_pose(puck_name)["pos"])
                if np.linalg.norm(final_pos - target_pos) <= target_radius:
                    return True
        except Exception:
            pass
        return False
