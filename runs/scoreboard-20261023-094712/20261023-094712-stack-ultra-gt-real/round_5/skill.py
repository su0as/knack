import math

def run(robot):
    # Constants
    PRE_GRASP_Z = 0.08      # well above cube for approach
    GRASP_Z = 0.015         # tool point at cube center (pads at ~0.0025)
    LIFT_Z = 0.12           # safe transport height
    STACK_Z = 0.045         # red cube center when stacked on blue (blue top 0.03 + 0.015)
    STACK_CLEARANCE = 0.005 # extra height before final descent
    APPROACH_SPEED = 0.15
    PRECISION_SPEED = 0.05
    TRANSPORT_SPEED = 0.10

    # --- Pick up red cube ---
    # Fresh observation for grasp approach
    obs = robot.observe()
    if "red_cube" not in obs["objects"]:
        robot.home()
        return False
    red_pos = obs["objects"]["red_cube"]["pos"]
    red_yaw = obs["objects"]["red_cube"]["yaw"]

    # Approach from above
    try:
        robot.move_to(red_pos[0], red_pos[1], PRE_GRASP_Z, yaw=red_yaw, speed=APPROACH_SPEED)
    except MotionError:
        robot.home()
        return False

    # Descend to grasp height
    try:
        robot.move_to(red_pos[0], red_pos[1], GRASP_Z, yaw=red_yaw, speed=PRECISION_SPEED)
    except MotionError:
        robot.home()
        return False

    # Grasp with one retry on fresh observation
    if not robot.grasp():
        obs = robot.observe()
        if "red_cube" not in obs["objects"]:
            robot.home()
            return False
        red_pos = obs["objects"]["red_cube"]["pos"]
        red_yaw = obs["objects"]["red_cube"]["yaw"]
        try:
            robot.move_to(red_pos[0], red_pos[1], GRASP_Z, yaw=red_yaw, speed=PRECISION_SPEED)
        except MotionError:
            robot.home()
            return False
        if not robot.grasp():
            robot.home()
            return False

    robot.wait(0.1)  # let fingers settle

    # Verify holding
    if robot.holding() != "red_cube":
        robot.release()
        robot.home()
        return False

    # Lift red cube
    try:
        robot.move_to(red_pos[0], red_pos[1], LIFT_Z, yaw=red_yaw, speed=TRANSPORT_SPEED)
    except MotionError:
        robot.release()
        robot.home()
        return False

    # --- Stack on blue cube ---
    # Fresh observation for blue cube position (with retry)
    blue_pos = None
    blue_yaw = None
    for _ in range(2):
        obs = robot.observe()
        if "blue_cube" in obs["objects"]:
            blue_pos = obs["objects"]["blue_cube"]["pos"]
            blue_yaw = obs["objects"]["blue_cube"]["yaw"]
            break
        robot.wait(0.1)
    if blue_pos is None:
        robot.release()
        robot.home()
        return False

    stack_x, stack_y = blue_pos[0], blue_pos[1]

    # Verify still holding before transport
    if robot.holding() != "red_cube":
        robot.home()
        return False

    # Move above blue cube, align with blue yaw
    try:
        robot.move_to(stack_x, stack_y, LIFT_Z, yaw=blue_yaw, speed=TRANSPORT_SPEED)
    except MotionError:
        robot.release()
        robot.home()
        return False

    # Descend to stack height with clearance
    target_z = STACK_Z + STACK_CLEARANCE
    try:
        result = robot.move_to(stack_x, stack_y, target_z, yaw=blue_yaw, speed=PRECISION_SPEED)
    except MotionError:
        robot.release()
        robot.home()
        return False

    # Verify descent: if still above STACK_Z + 0.01, descend further
    achieved_z = result["pos"][2]
    if achieved_z > STACK_Z + 0.01:
        try:
            robot.move_by(dz=-(achieved_z - STACK_Z - 0.001), speed=PRECISION_SPEED)
        except MotionError:
            robot.release()
            robot.home()
            return False

    robot.wait(0.1)  # let cube seat

    # Release at stack height
    robot.release()

    # Retract slightly to avoid knocking the stack
    try:
        robot.move_by(dz=0.03, speed=TRANSPORT_SPEED)
    except MotionError:
        pass

    robot.home()
    return True
