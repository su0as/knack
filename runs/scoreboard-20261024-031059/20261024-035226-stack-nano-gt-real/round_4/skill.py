# the complete skill module
import math, numpy as np, itertools, functools, collections

def run(robot):
    """
    Stack the red cube on top of the blue cube and release it.
    """
    MAX_OVERALL = 3
    PLACEMENT_OFFSET_THRESHOLD = 0.015   # maximum allowed xy offset (m)

    for overall_attempt in range(MAX_OVERALL):
        # --------------------------------------------------------------
        # 1. Perceive target cubes (one extra observation if needed)
        obs = robot.observe()
        objs = obs.get("objects", {})
        red = objs.get("red_cube")
        blue = objs.get("blue_cube")
        if red is None or blue is None:
            robot.log("Target cubes missing – retrying perception")
            obs2 = robot.observe()
            objs2 = obs2.get("objects", {})
            red = objs2.get("red_cube")
            blue = objs2.get("blue_cube")
            if red is None or blue is None:
                robot.log("Cubes still missing after retry")
                return False

        # --------------------------------------------------------------
        # 2. Pick the red cube
        rx, ry, rz = red["pos"]
        # pick height: centre + clearance (0.02 m + 0.01 m)
        pick_z = rz + 0.03

        # robust move_to with one short‑stop recovery
        for pick_retry in range(2):
            try:
                result = robot.move_to(rx, ry, pick_z, speed=0.07)
                if result["ok"]:
                    break
                # short‑stop: shift a little in xy
                shift = 0.02 if result["error_m"] > 0.005 else -0.02
                rx += shift
                ry += shift
                robot.log(f"Pick short‑stop error_m={result['error_m']:.3f}")
            except Exception:
                robot.log("Pick move exception")
                return False

        # close fingers and seat
        robot.grasp()
        robot.move_by(dz=0.01, speed=0.07)   # small seat down

        # --------------------------------------------------------------
        # 3. Lift clear of the red cube
        robot.move_by(dz=0.02, speed=0.07)

        # --------------------------------------------------------------
        # 4. Move above the blue cube for placement
        bx, by, bz = blue["pos"]
        place_z = bz + 0.015 + 0.015   # top of blue + clearance

        # --------------------------------------------------------------
        # 5. Placement attempts (up to 2)
        for placement_try in range(2):
            # ----- try to move to the placement target -----
            try:
                robot.move_to(bx, by, place_z, speed=0.07)
            except Exception:
                robot.log("Place move exception – backing off")
                # back‑off in height and shift target toward observed red centre
                place_z -= 0.02
                # get current red position to compute offset
                obs2 = robot.observe()
                red2 = obs2.get("objects", {}).get("red_cube")
                if red2:
                    dx = red2["pos"][0] - bx
                    dy = red2["pos"][1] - by
                    offset = math.hypot(dx, dy)
                    if offset > 1e-5 and offset > PLACEMENT_OFFSET_THRESHOLD:
                        scale = PLACEMENT_OFFSET_THRESHOLD / offset
                        bx += dx * scale
                        by += dy * scale
                        robot.log(f"Adjusted placement target, new offset={offset*scale:.3f}")
                # retry the move in the next iteration of placement_try
                continue

            # ----- verify that the red cube is still held -----
            obs2 = robot.observe()
            red2 = obs2.get("objects", {}).get("red_cube")
            if red2 is None:
                robot.log("Red disappeared during placement")
                if overall_attempt == MAX_OVERALL - 1:
                    return False
                break

            # compute current xy offset
            dx = red2["pos"][0] - bx
            dy = red2["pos"][1] - by
            xy_offset = math.hypot(dx, dy)

            # if offset still too large, adjust target once more
            if xy_offset > PLACEMENT_OFFSET_THRESHOLD:
                scale = PLACEMENT_OFFSET_THRESHOLD / xy_offset
                bx += dx * scale
                by += dy * scale
                robot.log(f"Placement offset {xy_offset:.3f} > thr, adjusted target")
                # retry the move
                continue

            # ----- release the cube -----
            robot.release()
            if robot.holding() is None:
                return True   # success
            else:
                # release failed – simple recovery: lower and re‑grasp
                robot.log("Release verification failed, still holding")
                robot.move_by(dz=-0.02, speed=0.07)
                robot.grasp()
                # fall through to retry the overall sequence
                break

        # if we exit the inner loop without succeeding, try next overall attempt
        if overall_attempt == MAX_OVERALL - 1:
            return False

    return False
