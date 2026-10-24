"""OpenCV 5 perception on rendered RGB-D cameras: detections are compared with the simulator's true poses."""
import numpy as np
import pytest

from knack.sim import SimEnv
from knack.tasks import TASKS

cv2 = pytest.importorskip("cv2")


def _render_ok():
    env = SimEnv(TASKS["lift"], 0)
    ok = env.render("overhead") is not None
    env.close()
    return ok


@pytest.mark.parametrize("task_id", list(TASKS))
def test_vision_finds_objects_and_fixtures(task_id):
    if not _render_ok():
        pytest.skip("no OpenGL in this environment")
    from knack.vision import VisionPerception

    errs, misses, lookups, fix_errs = [], 0, 0, []
    for seed in range(4):
        env = SimEnv(TASKS[task_id], 7000 + seed, realism="vision")
        v = VisionPerception(env)
        v.observe()
        s = v.summary()
        print(task_id, seed, s)
        errs.append(s["pos_err_mm_median"])
        misses += s["misses"]
        lookups += s["lookups"]
        fix_errs += list(s["fixture_err_mm"].values())
        assert sorted(s["fixtures_mapped"]) == sorted(env.fixture_spec)
        v.close()
        env.close()
    assert misses <= max(1, lookups // 8), f"{misses}/{lookups} objects not seen at episode start"
    assert np.nanmedian(errs) < 10.0, f"median position error {np.nanmedian(errs)} mm"
    if fix_errs:
        assert max(fix_errs) < 12.0, f"fixture error {max(fix_errs)} mm"


def test_vision_mode_robot_api():
    if not _render_ok():
        pytest.skip("no OpenGL in this environment")
    from knack.robot import SimRobot
    from knack.vision import PerceptionError, VisionPerception

    env = SimEnv(TASKS["stack"], 7100, realism="vision")
    robot = SimRobot(env, vision=VisionPerception(env), obs_noise=0.0)
    obs = robot.observe()
    assert set(obs["objects"]) <= set(env.obj_spec) and obs["objects"]
    for name, e in obs["objects"].items():
        true, _ = env.object_pose(name)
        assert np.linalg.norm(np.array(e["pos"]) - true) < 0.015
    assert issubclass(PerceptionError, LookupError)
    env.close()
