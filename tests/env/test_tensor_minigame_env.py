import pytest
import random
import numpy as np
import time

from freeciv_gym.envs.freeciv_minitask_env import MinitaskType
from freeciv_gym.envs.freeciv_wrapper.tensor_wrapper import TensorWrapper
from freeciv_gym.envs.freeciv_wrapper.utils import *
from freeciv_gym.freeciv.utils.port_list import DEV_PORT_LIST

import warnings

# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings("ignore", message=".*The obs returned by the .* method.*")

import gymnasium as gym

client_port = random.choice(DEV_PORT_LIST)


def get_client_port():
    """
    randomly sample from DEV_PORT_LIST to get a client port different from the last one
    """
    global client_port
    if (result := random.choice(DEV_PORT_LIST)) != client_port:
        client_port = result
        time.sleep(2)
        return client_port
    else:
        return get_client_port()


@pytest.fixture
def env():
    env = TensorWrapper(
        env=gym.make("freeciv/FreecivMinitask-v0", client_port=get_client_port())
    )
    yield env
    env.close()


@pytest.fixture(params=MinitaskType.list())
def task_name(request):
    yield request.param


def test_minitask_tensor_env(env, task_name):
    # TODO: test other tasks, only buildcity and battle saves are supported now
    if task_name not in ["buildcity", "battle"]:
        _, _ = env.reset()
        return

    obs, _ = env.reset(minitask_pattern=task_name)
    unit_action_pos = np.where(obs["unit_action_type_mask"] == 1)
    idx = np.random.randint(len(unit_action_pos[0]))
    act_unit = {
        "actor_type": 1,
        "unit_id": unit_action_pos[0][idx],
        "unit_action_type": unit_action_pos[1][idx],
    }
    obs, reward, terminated, truncated, info = env.step(act_unit)

    city_action_pos = np.where(obs["city_action_type_mask"] == 1)
    if len(city_action_pos[0]) > 0:
        idx = np.random.randint(len(city_action_pos[0]))
        act_city = {
            "actor_type": 2,
            "city_id": city_action_pos[0][idx],
            "city_action_type": city_action_pos[1][idx],
        }
        obs, reward, terminated, truncated, info = env.step(act_city)
    else:
        assert task_name == "buildcity" or task_name == "battle"

    gov_action_pos = np.where(obs["gov_action_type_mask"] == 1)
    action_type = np.random.choice(gov_action_pos[0])
    act_gov = {
        "actor_type": 3,
        "gov_action_type": action_type,
    }
    obs, reward, terminated, truncated, info = env.step(act_gov)
