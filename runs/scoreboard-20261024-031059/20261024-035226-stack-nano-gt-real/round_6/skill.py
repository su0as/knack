# the complete skill module
import math, numpy as np, itertools, functools, collections

def run(robot):
    """
    Stack the red cube on top of the blue cube and release it.
    Improvements:
      • Simple grasp verification – abort on failure instead of fragile re‑grasp.
      • Small, capped placement‑offset correction (max 0.02 m) to stay in reach.
      • Limited retries for pick and placement while keeping a 3‑attempt overall budget.
    """
    MAX_OVERALL = 3  # overall attempts before giving up

    for overall_attempt in range(MAX_OVERALL):
        # --------------------------------------------------------------
        # 1. Perceive (with one extra observation if needed)
        obs = robot.observe()
        objs = obs.get("objects", {})
        red = objs.get("red_cube")
        blue = objs.get("blue_cube")
        if red is None or blue is None:
            robot.log("Target cubes missing – retrying perception")
            obs = robot.observe()
            objs = obs.get("objects", {})
            red = objs.get("red_cube")
            blue = objs.get("blue_cube")
            if red is None or blue is None:
                robot.log("Cubes still missing after retry")
                return False

        # --------------------------------------------------------------
        # 2. Pick the red cube
        rx, ry, rz = red["pos"]
        pick_z = rz + 0.025  # a little above centre for safe grasp
        pick_ok = False
        for pick_retry in range(2):
            try:
                result = robot.move_to(rx, ry, pick_z, speed=0.07)
                if result["ok"]:
                    pick_ok = True
                    break
                # if move_to fails we simply retry (short‑stop correction omitted for simplicity)
            except Exception:
                continue
        if not pick_ok:
            continue  # try next overall attempt

        robot.grasp()
        # verify that the red cube is actually held
        if robot.holding() != "red_cube":
            robot.log("Grasp verification failed")
            if overall_attempt == MAX_OVERALL - 1:
                return False
            continue  # restart whole sequence

        # --------------------------------------------------------------
        # 3. Lift clear of the red cube
        robot.move_by(dz=0.02, speed=0.07)

        # --------------------------------------------------------------
        # 4. Move above the blue cube for placement
        bx, by, bz = blue["pos"]
        place_z = bz + 0.03  # approximate centre height for the red cube on top

        # up to two tries for the placement move (offset check may abort)
        for placement_try in range(2):
            try:
                robot.move_to(bx, by, place_z, speed=0.07)
            except Exception:
                robot.log("Place move failed")
                if overall_attempt == MAX_OVERALL - 1:
                    return False
                break  # abort this overall attempt

            # Verify that the red cube is still held and that its perceived xy offset is small
            obs2 = robot.observe()
            red2 = obs2.get("objects", {}).get("red_cube")
            if red2 is None:
                robot.log("Red disappeared during placement")
                if overall_attempt == MAX_OVERALL - 1:
                    return False
                break

            dx = red2["pos"][0] - bx
            dy = red2["pos"][1] - by
            xy_offset = math.hypot(dx, dy)

            if xy_offset < 0.02:  # good enough – proceed to release
                robot.release()
                if robot.holding() is None:
                    return True  # success
                else:
                    robot.log("Release verification failed, still holding")
                    # abort this overall attempt – will retry from the top
                    if overall_attempt == MAX_OVERALL - 1:
                        return False
                    break

            # Offset too large – nudge the target toward the observed red centre
            # but keep the shift small and bounded
            shift_x = dx * 0.1
            shift_y = dy * 0.1
            max_shift = 0.02
            shift_x = math.copysign(min(abs(shift_x), max_shift), shift_x)
            shift_y = math.copysign(min(abs(shift_y), max_shift), shift_y)
            bx += shift_x
            by += shift_y

            # after adjusting, retry the placement move (if attempts remain)
            if placement_try == 1:  # exhausted placement retries
                if overall_attempt == MAX_OVERALL - 1:
                    return False
                break
            continue  # retry the placement move with the new target

        # If we exit the inner loop without returning, we will retry the whole
        # sequence (subject to the overall attempt limit).
        if overall_attempt == MAX_OVERALL - 1:
            return False

    return False
