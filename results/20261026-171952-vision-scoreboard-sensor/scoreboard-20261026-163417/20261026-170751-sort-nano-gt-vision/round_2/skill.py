# skill module
import math

def run(robot):
    """
    Place the red cube into the red tray and the blue cube into the blue tray.
    Returns True if both placements succeed.
    """
    # ----- safety limits -------------------------------------------------
    SAFE_X_MIN, SAFE_X_MAX = 0.04, 0.32
    SAFE_Y_MIN, SAFE_Y_MAX = -0.26, 0.26
    SAFE_Z_MIN, SAFE_Z_MAX = 0.014, 0.26

    # ----- parameters ----------------------------------------------------
    FORWARD_OFFSET = 0.01          # m, small enough to stay inside workspace
    CONTACT_OFFSET = 0.005         # m, just touch the top of the cube
    RELEASE_HEIGHT = 0.015         # m, cube centre height (table surface is 0)
    LATERAL_FALLBACK = 0.02        # m, small shift if tray approach fails
    MAX_GRASP_RETRIES = 2
    MAX_ATTEMPTS = 30
    LOW_SPEED = 0.05
    APPROACH_SPEED = 0.07

    # ----- state ---------------------------------------------------------
    placed = {"red": False, "blue": False}
    attempts = 0
    # remember previous centre for stability check
    prev_center = {}
    # count grasp failures per colour
    grasp_retries = {"red": 0, "blue": 0}

    while not all(placed.values()) and attempts < MAX_ATTEMPTS:
        attempts += 1
        robot.log(f"Attempt {attempts}")
        obs = robot.observe()
        objs = obs.get("objects", {})
        fixtures = obs.get("fixtures", {})

        # ----- extract cube and tray poses ---------------------------------
        cube_info = {}
        for name, data in objs.items():
            if data["shape"] == "cube":
                cube_info[data["color"]] = {
                    "pose": data["pos"],
                    "yaw": data["yaw"],
                    "name": name,
                }

        tray_info = {}
        for name, data in fixtures.items():
            if data["kind"] == "tray":
                tray_info[data["color"]] = data["pos"]

        # ----- process each colour -----------------------------------------
        for colour in ("red", "blue"):
            if placed[colour]:
                continue
            cube = cube_info.get(colour)
            tray = tray_info.get(colour)
            if not cube or not tray:
                continue

            # ----- stability check (same centre for two frames) -------------
            cur_center = tuple(cube["pose"])
            if prev_center.get(colour) is not None:
                if math.dist(prev_center[colour], cur_center) > 0.002:  # >2 mm
                    robot.log(f"Cube {colour} moved, resetting stability")
                    prev_center[colour] = cur_center
                    grasp_retries[colour] = 0
                    continue
            else:
                prev_center[colour] = cur_center

            # ----- pick‑up ---------------------------------------------------
            # safe approach point (forward a little in gripper direction)
            g_yaw = cube["yaw"]
            dx = math.cos(g_yaw) * FORWARD_OFFSET
            dy = math.sin(g_yaw) * FORWARD_OFFSET
            app_x = cube["pose"][0] + dx
            app_y = cube["pose"][1] + dy
            # clip to safe workspace
            app_x = max(SAFE_X_MIN, min(SAFE_X_MAX, app_x))
            app_y = max(SAFE_Y_MIN, min(SAFE_Y_MAX, app_y))
            app_z = cube["pose"][2] + 0.015   # lift a bit above the cube
            contact_z = app_z - 0.01          # just touch the top

            # move to approach point
            try:
                robot.log(f"Moving to approach {colour} cube at "
                          f"({app_x:.3f},{app_y:.3f},{app_z:.3f})")
                resp = robot.move_to(app_x, app_y, app_z,
                                     yaw=g_yaw, speed=APPROACH_SPEED)
                if not resp["ok"]:
                    raise Exception("blocked on approach")
            except Exception as e:
                robot.log(f"Approach move failed: {e}")
                continue

            # descend to contact
            try:
                robot.log("Descending to contact")
                resp = robot.move_to(app_x, app_y, contact_z,
                                     yaw=g_yaw, speed=LOW_SPEED)
                if not resp["ok"]:
                    raise Exception("blocked on contact")
            except Exception as e:
                robot.log(f"Contact move failed: {e}")
                continue

            # close grasp
            robot.log("Closing grasp")
            if not robot.grasp():
                robot.log("Grasp failed")
                robot.release()
                grasp_retries[colour] += 1
                if grasp_retries[colour] >= MAX_GRASP_RETRIES:
                    robot.log(f"Too many grasp failures for {colour}, skipping")
                    robot.release()
                    prev_center[colour] = None
                    continue
                else:
                    # retry the whole attempt (next loop iteration will re‑observe)
                    continue
            # verify that we really hold the intended cube
            held = robot.holding()
            if held != cube["name"]:
                robot.log(f"Holding check failed: expected {cube['name']}, got {held}")
                robot.release()
                continue

            # ----- move to release zone ------------------------------------
            tray_x, tray_y = tray
            release_z_above = RELEASE_HEIGHT + 0.02   # a little above the tray floor
            release_z_target = RELEASE_HEIGHT        # just above the floor

            # try the nominal tray position, then simple fallbacks
            def try_approach(x, y, description):
                try:
                    robot.log(f"Moving to release zone over {colour} tray at "
                              f"({x:.3f},{y:.3f},{release_z_above:.3f})")
                    resp = robot.move_to(x, y, release_z_above,
                                         yaw=None, speed=APPROACH_SPEED)
                    if not resp["ok"]:
                        raise Exception("blocked on tray approach")
                    return True
                except Exception as e:
                    robot.log(f"{description} failed: {e}")
                    return False

            # 1) nominal position
            if not try_approach(tray_x, tray_y, "Tray approach"):
                # 2) shift a little in x
                if not try_approach(max(SAFE_X_MIN, min(SAFE_X_MAX, tray_x + LATERAL_FALLBACK)),
                                    tray_y, "Shifted x+ fallback"):
                    # 3) shift a little in y
                    if not try_approach(tray_x,
                                        max(SAFE_Y_MIN, min(SAFE_Y_MAX, tray_y + LATERAL_FALLBACK)),
                                        "Shifted y+ fallback"):
                        robot.log(f"All tray approaches failed for {colour}; skipping")
                        continue

            # lower to release height
            try:
                robot.log("Lowering to release height")
                resp = robot.move_to(tray_x, tray_y, release_z_target,
                                     yaw=None, speed=LOW_SPEED)
                if not resp["ok"]:
                    raise Exception("blocked on release descent")
            except Exception as e:
                robot.log(f"Release descent failed: {e}")
                continue

            # release the cube
            robot.log("Releasing cube")
            robot.release()

            # verify release; if still holding, try a small lift and release again
            if robot.holding() is not None:
                robot.log("Release check failed, retrying lift")
                try:
                    robot.move_to(tray_x, tray_y, release_z_above,
                                  yaw=None, speed=APPROACH_SPEED)
                    robot.release()
                except Exception as e:
                    robot.log(f"Retry release move failed: {e}")
                    continue

            # success for this colour
            placed[colour] = True
            robot.log(f"Successfully placed {colour} cube")
            # reset stability flag so next episode starts fresh
            prev_center[colour] = None

        # small pause to let the simulation settle
        robot.wait(0.2)

    success = all(placed.values())
    robot.log(f"Skill finished, success={success}")
    return success
