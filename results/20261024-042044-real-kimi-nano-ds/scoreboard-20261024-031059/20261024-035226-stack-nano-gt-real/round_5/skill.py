# the complete skill module
import math

def run(robot):
    """
    Stack the red cube on top of the blue cube and release it.
    """
    MAX_OVERALL = 3  # overall attempts before giving up

    for overall_attempt in range(MAX_OVERALL):
        # --------------------------------------------------------------
        # 1. Perceive red and blue (one extra observation if needed)
        obs = robot.observe()
        objs = obs.get("objects", {})
        red = objs.get("red_cube")
        blue = objs.get("blue_cube")
        if red is None or blue is None:
            # retry once
            obs = robot.observe()
            objs = obs.get("objects", {})
            red = objs.get("red_cube")
            blue = objs.get("blue_cube")
            if red is None or blue is None:
                # still missing – skip this overall attempt
                continue

        # --------------------------------------------------------------
        # 2. Pick the red cube
        rx, ry, rz = red["pos"]
        pick_z = rz + 0.03                     # clearance above centre
        pick_ok = False
        for pick_retry in range(2):
            try:
                result = robot.move_to(rx, ry, pick_z, speed=0.07)
                if result["ok"]:
                    pick_ok = True
                    break
                # short‑stop: compute a small corrective shift
                dx = result["pos"][0] - rx
                dy = result["pos"][1] - ry
                err = result["error_m"]
                if err > 0.005:
                    # shift opposite to the error, max 0.005 m
                    shift_len = min(0.005, err)
                    shift_x = -dx / err * shift_len if err != 0 else 0
                    shift_y = -dy / err * shift_len if err != 0 else 0
                    rx += shift_x
                    ry += shift_y
                    robot.log(f"Pick short‑stop shift ({shift_x:.3f},{shift_y:.3f}) err={err:.3f}")
            except Exception:
                robot.log("Pick move exception")
                # retry with same target
                continue
            # if we get here the move succeeded
            break

        if not pick_ok:
            # could not reach after retries – go to next overall attempt
            continue

        # grasp and seat the cube
        robot.grasp()
        robot.move_by(dz=0.01, speed=0.07)    # small seat down

        # quick verification; if not holding red, try one re‑grasp
        if robot.holding() != "red_cube":
            robot.log("Grasp verification failed – attempting re‑grasp")
            robot.release()
            # lift slightly to clear any obstruction
            robot.move_by(dz=0.02, speed=0.07)
            robot.grasp()
            robot.move_by(dz=-0.01, speed=0.07)  # back to seat height
            if robot.holding() != "red_cube":
                # give up this overall attempt
                continue

        # --------------------------------------------------------------
        # 3. Lift clear of the red cube
        robot.move_by(dz=0.02, speed=0.07)

        # --------------------------------------------------------------
        # 4. Move above the blue cube for placement
        bx, by, bz = blue["pos"]
        place_z = bz + 0.015 + 0.015   # clearance above blue

        placement_ok = False
        for placement_retry in range(2):
            try:
                result = robot.move_to(bx, by, place_z, speed=0.07)
                if result["ok"]:
                    placement_ok = True
                    break

                # short‑stop recovery: back‑off height and shift target toward red
                robot.log("Placement short‑stop")
                robot.move_by(dz=-0.01, speed=0.07)  # back‑off a little

                # re‑observe red position
                obs2 = robot.observe()
                red2 = obs2.get("objects", {}).get("red_cube")
                if red2 is None:
                    robot.log("Red disappeared during placement recovery")
                    break

                # compute offset from blue centre
                dx = red2["pos"][0] - bx
                dy = red2["pos"][1] - by
                offset = math.hypot(dx, dy)
                if offset > 0.015:
                    # move target a fraction toward red centre (halfway)
                    factor = 0.5
                    bx += factor * dx
                    by += factor * dy
                    robot.log(f"Adjusted placement target by offset {offset:.3f}")

                # retry the move with possibly adjusted target
                result = robot.move_to(bx, by, place_z, speed=0.07)
                if result["ok"]:
                    placement_ok = True
                    break
                # if still not ok, fall through to retry loop
            except Exception:
                robot.log("Place move exception")
                # retry with same target
                continue

            # if we exhausted retries, break to outer loop
            break

        if not placement_ok:
            # exhausted placement retries – go to next overall attempt
            continue

        # --------------------------------------------------------------
        # 5. Release and verify success
        robot.release()
        robot.wait(0.2)  # let the system settle

        if robot.holding() is None:
            return True  # success

        robot.log("Release verification failed – still holding")
        # simple recovery: lower a bit and release again (once)
        robot.move_by(dz=-0.02, speed=0.07)
        robot.release()
        robot.wait(0.2)
        if robot.holding() is None:
            return True

        # if we reach here the release still failed – retry the whole sequence
        # (subject to the overall attempt limit)

    return False
