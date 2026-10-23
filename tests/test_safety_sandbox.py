import numpy as np
import pytest

from knack.robot import MotionError, SimRobot
from knack.safety import Limits, RobotHalt, SafetyShield, SafetyViolation
from knack.sandbox import SkillCompileError, compile_skill, extract_code, validate
from knack.sim import SimEnv
from knack.tasks import get_task


def test_shield_clamps_small_and_halts_large():
    s = SafetyShield(Limits())
    p = s.filter_target([0.2, 0.0, 0.0])
    assert p[2] == pytest.approx(0.014)
    assert s.events[-1]["action"] == "clamp"
    with pytest.raises(SafetyViolation):
        s.filter_target([0.2, 0.0, -0.1])
    with pytest.raises(SafetyViolation):
        s.filter_target([float("nan"), 0, 0.1])
    assert s.filter_speed(5.0) == Limits().max_speed
    assert s.filter_speed(None) == Limits().default_speed


def test_joint_step_limit():
    s = SafetyShield(Limits(max_joint_speed=1.0))
    q = s.limit_joint_step(np.zeros(5), np.ones(5), 0.02)
    assert np.allclose(q, 0.02)


def test_halt_is_not_catchable_by_except_exception():
    env = SimEnv(get_task("lift"), 0)
    robot = SimRobot(env)
    code = """
def run(robot):
    try:
        robot.move_to(0.2, 0.0, -0.2)
    except Exception:
        return 'swallowed'
    return 'no'
"""
    fn = compile_skill(code)
    with pytest.raises(RobotHalt):
        fn(robot)
    with pytest.raises(RobotHalt):
        robot.observe()  # stays halted


def test_unreachable_is_catchable():
    env = SimEnv(get_task("lift"), 0)
    robot = SimRobot(env)
    with pytest.raises(MotionError):
        robot.move_to(0.31, 0.25, 0.25)
    assert robot.observe()["time"] >= 0


@pytest.mark.parametrize("bad", [
    "import os\ndef run(robot):\n    pass\n",
    "def run(robot):\n    open('x')\n",
    "def run(robot):\n    robot._env\n",
    "def run(robot):\n    try:\n        pass\n    except:\n        pass\n",
    "def run(robot):\n    eval('1')\n",
    "import numpy as np\ndef run(robot):\n    np.save('x', 1)\n",
    "def run(robot):\n    raise BaseException()\n",
    "def helper(robot):\n    pass\n",
    "def run(robot)\n    pass\n",
])
def test_validate_rejects(bad):
    assert validate(bad)
    with pytest.raises(SkillCompileError):
        compile_skill(bad)


def test_validate_accepts_normal_code():
    code = "import math\nimport numpy as np\nfrom math import pi\n\ndef run(robot):\n    a = np.array([1.0, 2.0])\n    return float(math.hypot(*a)) > pi\n"
    assert validate(code) == []
    assert compile_skill(code)(None) is False


def test_extract_code():
    txt = "<notes>- x</notes>\nsome words\n```python\nimport math\n\ndef run(robot):\n    return True\n```\n"
    assert extract_code(txt).startswith("import math")
    assert extract_code("no code here") is None
