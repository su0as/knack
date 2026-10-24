# the complete skill module
import math, numpy as np, itertools, functools, collections

def run(robot):
    """
    Stack the red cube on top of the blue cube and release it.
    The implementation now includes:
      • perception sanity check with one retry,
      • seated grasp verification,
      • placement‑offset validation before release,
      • limited retries for grasp and placement,
      • simple recovery on release failure.
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
        pick_z = rz + 0.02                     # 2 cm above centre
        try:
            robot.move_to(rx, ry, pick_z, speed=0.07)
        except Exception:
            robot.log("Pick move failed")
            return False

        robot.grasp()
        robot.move_by(dz=0.01, speed=0.07)    # seat the cube
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
        place_z = bz + 0.015 + 0.015           # centre height of red on blue

        # up to two tries for the placement move (offset check may abort)
        for placement_try in range(2):
            try:
                robot.move_to(bx, by, place_z, speed=0.07)
            except Exception:
                robot.log("Place move failed")
                if overall_attempt == MAX_OVERALL - 1:
                    return False
                break  # abort this overall attempt

            # Verify that the red cube is still held and that its perceived
            # xy offset from the target is small enough.
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
            if xy_offset < 0.02:          # good enough
                # ------------------------------------------------------
                # 5. Release and verify success
                robot.release()
                if robot.holding() is None:
                    return True  # success
                else:
                    robot.log("Release verification failed, still holding")
                    # simple recovery: lower, re‑grasp, and try again
                    robot.move_by(dz=-0.02, speed=0.07)
                    robot.grasp()
                    # fall through to retry the overall sequence
                    break
            else:
                # offset too large – abort placement and retry the move
                robot.log(f"Placement xy offset {xy_offset:.3f} > 0.02, retrying")
                if placement_try == 1:    # exhausted placement retries
                    if overall_attempt == MAX_OVERALL - 1:
                        return False
                    break  # go to next overall attempt
                # otherwise retry the placement move
                continue

        # If we exit the inner loop without returning, we will retry the
        # whole sequence (subject to the overall attempt limit).
        if overall_attempt == MAX_OVERALL - 1:
            return False

    return False
