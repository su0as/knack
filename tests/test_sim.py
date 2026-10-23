import numpy as np
import pytest

from knack.kinematics import HOME_TCP, fk
from knack.robot import SimRobot
from knack.sim import SimEnv
from knack.tasks import TASKS, get_task


@pytest.mark.parametrize("task_id", list(TASKS))
def test_scene_builds_and_settles(task_id):
    task = get_task(task_id)
    for seed in range(5):
        env = SimEnv(task, seed)
        # arm holds the home pose (gravity compensation + position control)
        assert np.linalg.norm(env.tcp() - np.array(HOME_TCP)) < 0.005
        # model TCP agrees with the analytic FK used by IK
        assert np.linalg.norm(env.tcp() - fk(env.arm_q())["tcp"]) < 0.003
        for o in task.objects:
            pos, _ = env.object_pose(o.name)
            assert abs(pos[2] - o.rest_z) < 0.004, (task_id, seed, o.name, pos)
        ok, _ = task.success(env)
        assert not ok, f"{task_id} seed {seed} is already solved at reset"
        env.close()


def test_layout_is_deterministic():
    t = get_task("sort")
    a, b = SimEnv(t, 42), SimEnv(t, 42)
    assert a.layout == b.layout
    assert SimEnv(t, 43).layout != a.layout


def test_observe_shapes():
    env = SimEnv(get_task("tray"), 3)
    robot = SimRobot(env)
    obs = robot.observe()
    assert set(obs["objects"]) == {"yellow_cube", "red_cube"}
    assert obs["fixtures"]["tray"]["kind"] == "tray"
    assert -0.79 <= obs["objects"]["red_cube"]["yaw"] <= 0.79
    assert obs["gripper"]["holding"] is None


def test_move_to_tracks_target():
    env = SimEnv(get_task("lift"), 1)
    robot = SimRobot(env)
    res = robot.move_to(0.17, 0.05, 0.06)
    assert res["ok"], res
    assert res["error_m"] < 0.005
    res = robot.move_by(dz=0.03)
    assert res["ok"]
