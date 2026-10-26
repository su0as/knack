import math

def run(robot):
    # Safety: start from a known pose
    robot.home()

    # Get current scene perception
    obs = robot.observe()
    objects = obs.get('objects', {})

    # Ensure both cubes are visible
    if 'red_cube' not in objects or 'blue_cube' not in objects:
        robot.log("Missing cubes in observation")
        return False

    red_pose = objects['red_cube']
    blue_pose = objects['blue_cube']

    red_pos = red_pose['pos']
    blue_pos = blue_pose['pos']
    red_yaw = red_pose['yaw']
    blue_yaw = blue_pose['yaw']

    # Helper to attempt a grasp with retries
    def attempt_grasp(target_pos, target_yaw, desc):
        max_tries = 2
        for i in range(max_tries):
            # Approach from above
            above_z = target_pos[2] + 0.08  # 8 cm above the object
            move_res = robot.move_to(target_pos[0], target_pos[1], above_z,
                                     yaw=target_yaw, speed=0.2)
            if not move_res['ok']:
                robot.log(f"Failed to move above {desc}: {move_res}")
                continue

            # Descend to grasp height (just above the object's centre)
            grasp_z = target_pos[2] + 0.01  # 1 cm above centre to avoid hitting table
            move_res = robot.move_to(target_pos[0], target_pos[1], grasp_z,
                                     yaw=target_yaw, speed=0.05)
            if not move_res['ok']:
                robot.log(f"Failed to descend to grasp {desc}: {move_res}")
                robot.move_by(dz=0.08, speed=0.2)  # retreat up
                continue

            # Close fingers
            if robot.grasp():
                robot.log(f"Grasped {desc}")
                # Lift object
                lift_z = grasp_z + 0.1
                robot.move_to(target_pos[0], target_pos[1], lift_z,
                              yaw=target_yaw, speed=0.2)
                return True
            else:
                robot.log(f"Grasp attempt {i+1} failed for {desc}")
                robot.release()  # ensure open
                robot.move_by(dz=0.08, speed=0.2)  # retreat
        return False

    # 1. Pick up red cube
    if not attempt_grasp(red_pos, red_yaw, "red cube"):
        robot.log("Could not grasp red cube")
        return False

    # 2. Move red cube above blue cube (position where we will place)
    place_center_x = blue_pos[0]
    place_center_y = blue_pos[1]
    # Desired centre height for red cube when stacked on blue:
    place_z = blue_pos[2] + 0.03  # blue bottom + full cube height
    above_place_z = place_z + 0.08
    robot.move_to(place_center_x, place_center_y, above_place_z,
                  yaw=blue_yaw, speed=0.2)
    robot.move_to(place_center_x, place_center_y, place_z,
                  yaw=blue_yaw, speed=0.05)

    # 3. Release red cube onto blue cube
    robot.release()
    robot.log("Released red cube")

    # Retreat slightly to verify
    robot.move_by(dz=0.08, speed=0.2)

    # 4. Verify stacking: observe again and check relative pose
    obs2 = robot.observe()
    obj2 = obs2.get('objects', {})
    if 'red_cube' not in obj2 or 'blue_cube' not in obj2:
        robot.log("Lost track of cubes after release")
        return False

    red_pos2 = obj2['red_cube']['pos']
    blue_pos2 = obj2['blue_cube']['pos']

    # Expected offset: red centre should be directly above blue centre
    dx = red_pos2[0] - blue_pos2[0]
    dy = red_pos2[1] - blue_pos2[1]
    dz = red_pos2[2] - blue_pos2[2]

    xy_err = math.hypot(dx, dy)
    z_err = abs(dz - 0.03)  # allow small tolerance
    tolerance_xy = 0.02  # 2 cm
    tolerance_z = 0.01   # 1 cm

    if xy_err <= tolerance_xy and z_err <= tolerance_z:
        robot.log(f"Stack verified: xy_err={xy_err:.3f}, z_err={z_err:.3f}")
        return True
    else:
        robot.log(f"Stack failed: xy_err={xy_err:.3f}, z_err={z_err:.3f}")
        return False
