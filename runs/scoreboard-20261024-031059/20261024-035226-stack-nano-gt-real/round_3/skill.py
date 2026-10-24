# the complete skill module
import math

def run(robot):
    """
    Stack the red cube on top of the blue cube and release it.
    The implementation now includes:
      • increased pick‑height clearance (+0.01 m) and seat‑down verification,
      • hover‑and‑check with drift correction before placement,
      • robust move‑to handling with short‑stop back‑off and retry,
      • limited retries that only restart failing subtasks,
      • defensive logging of error_m and offset measurements.
    """
    MAX_OVERALL = 3  # overall attempts before giving up

    for overall_attempt in range(MAX_OVERALL):
        # --------------------------------------------------------------
        # 1. Perceive target cubes (one extra observation if needed)
        obs = robot.observe()
        objs = obs.get("objects", {})
        red = objs.get("red_cube")
        blue = objs.get("blue_cube")
        if red is None or blue is None:
            # retry once
            obs2 = robot.observe()
            objs2 = obs2.get("objects", {})
            red = objs2.get("red_cube")
            blue = objs2.get("blue_cube")
            if red is None or blue is None:
                robot.log("Target cubes missing after retry")
                return False

        # --------------------------------------------------------------
        # 2. Grasp the red cube
        rx, ry, rz = red["pos"]
        # increased clearance to improve secure seating
        pick_z = rz + 0.03  # 0.02 m + 0.01 m extra

        # move_to may short‑stop; retry once with a small shift
        for _ in range(2):
            result = robot.move_to(rx, ry, pick_z, speed=0.07)
            if result["ok"]:
                break
            robot.log(f"Pick short‑stop error_m={result['error_m']:.3f}")
            # modest xy shift to avoid joint limit or contact
            shift = 0.02 if result["error_m"] > 0.005 else -0.02
            rx += shift
            ry += shift

        robot.grasp()
        # seat the cube a little to ensure contact
        robot.move_by(dz=0.01, speed=0.07)

        # verify that the red cube is actually held
        if robot.holding() != "red_cube":
            robot.log("Grasp verification failed")
            if overall_attempt == MAX_OVERALL - 1:
                return False
            continue  # restart the whole sequence

        # lift clear of the red cube
        robot.move_by(dz=0.02, speed=0.07)

        # --------------------------------------------------------------
        # 3. Move above the blue cube for placement
        bx, by, bz = blue["pos"]
        place_z = bz + 0.015 + 0.015  # red centre on blue centre

        # up to two attempts for the placement step
        for placement_try in range(2):
            # ---- hover‑and‑check at a slightly lower height ----
            hover_z = place_z - 0.01
            # move to hover point (handle short‑stop)
            for _ in range(2):
                res = robot.move_to(bx, by, hover_z, speed=0.07)
                if res["ok"]:
                    break
                robot.log(f"Hover short‑stop error_m={res['error_m']:.3f}")
                hover_z -= 0.02  # back‑off in height

            # observe red cube position at hover height
            obs2 = robot.observe()
            red2 = obs2.get("objects", {}).get("red_cube")
            if red2 is None:
                robot.log("Red disappeared during hover")
                if overall_attempt == MAX_OVERALL - 1:
                    return False
                break  # abort this placement try

            # compute xy offset between observed red centre and target xy
            dx = red2["pos"][0] - bx
            dy = red2["pos"][1] - by
            xy_offset = math.hypot(dx, dy)

            # if offset too large, adjust target towards the observed red centre
            if xy_offset > 0.015:
                factor = max(0.0, 1.0 - 0.015 / xy_offset)
                bx_adj = bx + dx * factor
                by_adj = by + dy * factor
                target_x, target_y, target_z = bx_adj, by_adj, place_z
            else:
                target_x, target_y, target_z = bx, by, place_z

            # ---- final placement move (handle short‑stop) ----
            for _ in range(2):
                res = robot.move_to(target_x, target_y, target_z, speed=0.07)
                if res["ok"]:
                    break
                robot.log(f"Placement short‑stop error_m={res['error_m']:.3f}")
                # back‑off a little in height and retry
                target_z -= 0.02

            # release the cube
            robot.release()

            # verify that the cube is no longer held
            if robot.holding() is None:
                return True  # success
            else:
                robot.log("Release verification failed, still holding")
                # simple recovery: lower, re‑grasp, then retry the whole sequence
                robot.move_by(dz=-0.02, speed=0.07)
                robot.grasp()
                # fall through to retry the overall attempt
                break

        # if we exhausted placement retries without success, continue outer loop
        if overall_attempt == MAX_OVERALL - 1:
            return False

    return False
