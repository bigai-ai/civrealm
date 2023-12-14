import gymnasium
import time
import warnings

import numpy as np
import pytest
import itertools
from civrealm.envs.freeciv_minitask_env import MinitaskType, MinitaskDifficulty, MAX_ID
from civrealm.envs.freeciv_wrapper.utils import *
from civrealm.freeciv.utils.port_utils import Ports
from civrealm.freeciv.utils.freeciv_logging import fc_logger

@pytest.fixture(params=itertools.product(
    MinitaskType.list(),
    MinitaskDifficulty.list(),
    list(range(MAX_ID))
))
def env_with_id(request):
    minitask_type, difficulty, id = request.param
    env = gymnasium.make(
        "civrealm/FreecivMinitask-v0",
        client_port=Ports.get(),
    )
    yield env, {"type": minitask_type, "level": difficulty, "id": id}
    env.close()

def test_minitask_env(env_with_id):
    env, minitask_pattern = env_with_id
    obs, _ = env.reset(minitask_pattern=minitask_pattern)
    obs, reward, terminated, truncated, info = env.step(None)
