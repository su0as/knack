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
    FORWARD_OFFSET = 0.01          # m, small forward shift
    LIFT_OFFSET = 0.02             # m, extra lift to clear the cube
    CONTACT_OFFSET = 0.015         # m, distance from approach point to contact
    RELEASE_HEIGHT = 0.015         # m, nominal height of the tray floor
    LATERAL_FALLBACK = 0.02        # m, small shift if tray approach fails
    MAX_GRASP_RETRIES = 2
    MAX_ATTEMPTS = 30
    LOW_SPEED = 0.05
    APPROACH_SPEED = 0.07

    # ----- state ---------------------------------------------------------
    placed = {"red": False, "blue": False}
    attempts = 0
    prev_center = {}               # remember previous centre for stability
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

        # store only x,y for trays (fixture pos is [x, y, 0])
        tray_info = {}
        for name, data in fixtures.items():
            if data["kind"] == "tray":
                tray_info[data["color"]] = data["pos"][:2]   # (x, y)

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
            g_yaw = cube["yaw"]
            dx = math.cos(g_yaw) * FORWARD_OFFSET
            dy = math.sin(g_yaw) * FORWARD_OFFSET
            app_x = cube["pose"][0] + dx
            app_y = cube["pose"][1] + dy
            # clip to safe workspace
            app_x = max(SAFE_X_MIN, min(SAFE_X_MAX, app_x))
            app_y = max(SAFE_Y_MIN, min(SAFE_Y_MAX, app_y))
            # lift a bit higher to avoid collision
            app_z = cube["pose"][2] + LIFT_OFFSET
            contact_z = app_z - CONTACT_OFFSET

            # ---- move to approach point (with fallback) --------------------
            def try_approach(x, y, height, description):
                try:
                    robot.log(f"Moving to approach {colour} cube at "
                              f"({x:.3f},{y:.3f},{height:.3f})")
                    resp = robot.move_to(x, y, height,
                                         yaw=g_yaw, speed=APPROACH_SPEED)
                    if not resp["ok"]:
                        raise Exception("blocked on approach")
                    return True
                except Exception as e:
                    robot.log(f"{description} failed: {e}")
                    return False

            # try nominal position first
            if not try_approach(app_x, app_y, app_z, "Approach"):
                # try small lateral fallbacks
                fallback_offsets = [(LATERAL_FALLBACK, 0), (-LATERAL_FALLBACK, 0),
                                    (0, LATERAL_FALLBACK), (0, -LATERAL_FALLBACK)]
                for off_x, off_y in fallback_offsets:
                    nx, ny = max(SAFE_X_MIN, min(SAFE_X_MAX, app_x + off_x)), \
                             max(SAFE_Y_MIN, min(SAFE_Y_MAX, app_y + off_y))
                    if try_approach(nx, ny, app_z,
                                    f"Approach fallback {off_x:+.2f}/{off_y:+.2f}"):
                        break
                else:
                    # all fallbacks failed – skip this colour
                    robot.log(f"All approach attempts failed for {colour}; skipping")
                    continue

            # ---- descend to contact ----------------------------------------
            if not try_approach(app_x, app_y, contact_z, "Contact"):
                # fallback lateral shift for contact as well
                for off_x, off_y in fallback_offsets:
                    nx, ny = max(SAFE_X_MIN, min(SAFE_X_MAX, app_x + off_x)), \
                             max(SAFE_Y_MIN, min(SAFE_Y_MAX, app_y + off_y))
                    if try_approach(nx, ny, contact_z,
                                    f"Contact fallback {off_x:+.2f}/{off_y:+.2f}"):
                        break
                else:
                    robot.log(f"Contact move failed for {colour}; skipping")
                    continue

            # ---- close grasp -----------------------------------------------
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
                    # retry the whole attempt on next loop iteration
                    continue

            # verify that we really hold the intended cube
            held = robot.holding()
            if held != cube["name"]:
                robot.log(f"Holding check failed: expected {cube['name']}, got {held}")
                robot.release()
                continue

            # ----- move to release zone ------------------------------------
            # use only the (x, y) part of the tray; clip to safe workspace
            tray_x = max(SAFE_X_MIN, min(SAFE_X_MAX, tray[0]))
            tray_y = max(SAFE_Y_MIN, min(SAFE_Y_MAX, tray[1]))

            release_z_above = RELEASE_HEIGHT + 0.02   # a little above the tray floor
            release_z_target = RELEASE_HEIGHT        # just above the floor

            def try_place(x, y, height, description):
                try:
                    robot.log(f"Moving to release zone over {colour} tray at "
                              f"({x:.3f},{y:.3f},{height:.3f})")
                    resp = robot.move_to(x, y, height,
                                         yaw=None, speed=APPROACH_SPEED)
                    if not resp["ok"]:
                        raise Exception("blocked on tray approach")
                    return True
                except Exception as e:
                    robot.log(f"{description} failed: {e}")
                    return False

            # 1) nominal position
            if not try_place(tray_x, tray_y, release_z_above,
                             "Tray approach"):
                # 2) shift a little in x
                if not try_place(max(SAFE_X_MIN, min(SAFE_X_MAX, tray_x + LATERAL_FALLBACK)),
                                 tray_y, release_z_above,
                                 "Shifted x+ fallback"):
                    # 3) shift a little in y
                    if not try_place(tray_x,
                                     max(SAFE_Y_MIN, min(SAFE_Y_MAX, tray_y + LATERAL_FALLBACK)),
                                     release_z_above,
                                     "Shifted y+ fallback"):
                        robot.log(f"All tray approaches failed for {colour}; skipping")
                        continue

            # lower to release height
            if not try_place(tray_x, tray_y, release_z_target,
                             "Release descent"):
                robot.log(f"Release descent failed for {colour}; skipping")
                continue

            # release the cube
            robot.log("Releasing cube")
            robot.release()

            # verify release; if still holding, try a small lift and release again
            if robot.holding() is not None:
                robot.log("Release check failed, retrying lift")
                try:
                    # lift a bit, release, then lower again
                    robot.move_to(tray_x, tray_y, release_z_above,
                                  yaw=None, speed=APPROACH_SPEED)
                    robot.release()
                except Exception as e:
                    robot.log(f"Retry release move failed: {e}")
                    continue

            # success for this colour
            placed[colour] = True
            robot.log(f"Successfully placed {colour} cube")
            prev_center[colour] = None   # reset stability flag

        # small pause to let the simulation settle
        robot.wait(0.2)

    success = all(placed.values())
    robot.log(f"Skill finished, success={success}")
    return success
