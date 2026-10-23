import math

import numpy as np
import pytest

from knack.kinematics import SIM_ARM, IKError, fk, ik, roll_for_yaw, wrap_half_pi


@pytest.mark.parametrize("r", [0.12, 0.15, 0.18, 0.20])
@pytest.mark.parametrize("th", [-0.8, 0.0, 0.6])
@pytest.mark.parametrize("z", [0.016, 0.05, 0.09])
def test_ik_fk_roundtrip(r, th, z):
    p = np.array([r * math.cos(th), r * math.sin(th), z])
    q = ik(p, yaw=0.3)
    k = fk(q)
    assert np.allclose(k["tcp"], p, atol=1e-6)
    assert abs(k["pitch"] + math.pi / 2) < 1e-6  # straight down in the normal band
    assert abs(wrap_half_pi(k["yaw"] - 0.3)) < 1e-6


def test_tilts_near_edge_and_fails_far():
    q = ik([0.24, 0.0, 0.03])
    assert np.allclose(fk(q)["tcp"], [0.24, 0.0, 0.03], atol=1e-6)
    with pytest.raises(IKError):
        ik([0.6, 0.0, 0.05])
    with pytest.raises(IKError):
        ik([0.0, 0.0, 0.1])


def test_roll_for_yaw_symmetry():
    for pan in (-0.7, 0.0, 0.9):
        for yaw in (-1.2, 0.0, 0.4, 2.0):
            roll = roll_for_yaw(pan, yaw)
            assert -math.pi / 2 <= roll < math.pi / 2
            got = pan + math.pi / 2 - roll
            assert abs(wrap_half_pi(got - yaw)) < 1e-9


def test_joint_limits_respected():
    rng = np.random.default_rng(0)
    for _ in range(200):
        r, th, z = rng.uniform(0.1, 0.22), rng.uniform(-1.2, 1.2), rng.uniform(0.015, 0.15)
        try:
            q = ik([r * math.cos(th), r * math.sin(th), z])
        except IKError:
            continue
        for v, (lo, hi) in zip(q, SIM_ARM.joint_limits):
            assert lo - 1e-9 <= v <= hi + 1e-9
