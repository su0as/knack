import math

def run(robot):
    # 1. Start from a safe pose
    robot.home()

    # 2. Observe the scene to get cube poses
    obs = robot.observe()
    try:
        red = obs['objects']['red_cube']
        blue = obs['objects']['blue_cube']
    except KeyError:
        # If either cube is missing from perception, we cannot proceed.
        robot.log("Missing cube in observation")
        return False

    red_pos = red['pos']
    blue_pos = blue['pos']

    # Helper to attempt a motion and log failures
    def safe_move_to(x, y, z, yaw=None, speed=None):
        try:
            res = robot.move_to(x, y, z, yaw=yaw, speed=speed)
            if not res['ok']:
                robot.log(f"Move blocked to ({x:.3f},{y:.3f},{z:.3f})")
            return res
        except Exception as e:  # MotionError or others
            robot.log(f"Move exception: {e}")
            raise

    # 3. Position above the red cube (clearance 5 cm)
    above_red = [red_pos[0], red_pos[1], red_pos[2] + 0.05]
    safe_move_to(*above_red, speed=0.15)

    # 4. Descend to grasp height (centre of the cube)
    grasp_pose = [red_pos[0], red_pos[1], red_pos[2]]
    safe_move_to(*grasp_pose, speed=0.08)  # slower near the object

    # 5. Attempt to grasp
    if not robot.grasp():
        robot.log("Grasp failed on first attempt")
        # Retry once: lift a bit and try again
        safe_move_to(*above_red, speed=0.15)
        safe_move_to(*grasp_pose, speed=0.08)
        if not robot.grasp():
            robot.log("Second grasp attempt also failed")
            return False

    # 6. Verify we are holding something
    if robot.holding() is None:
        robot.log("Not holding after grasp")
        return False

    # 7. Lift the red cube to a safe clearance
    safe_move_to(*above_red, speed=0.15)

    # 8. Move above the blue cube (same clearance)
    above_blue = [blue_pos[0], blue_pos[1], blue_pos[2] + 0.05]
    safe_move_to(*above_blue, speed=0.15)

    # 9. Compute placement height for the red cube centre:
    #    blue top = blue_pos[2] + half_size; red centre when stacked = blue top + half_size
    #    Since both cubes are 0.03 m, half_size = 0.015 m.
    place_z = blue_pos[2] + 0.03  # blue centre + full cube size
    place_pose = [blue_pos[0], blue_pos[1], place_z]
    safe_move_to(*place_pose, speed=0.08)  # slow descent for stacking

    # 10. Release the red cube
    robot.release()

    # 11. Retreat a little to confirm release
    safe_move_to(*above_blue, speed=0.15)

    robot.log("Stack completed")
    return True
