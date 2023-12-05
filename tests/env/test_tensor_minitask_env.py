import gymnasium
import time
import warnings

import numpy as np
import pytest

from civrealm.envs.freeciv_minitask_env import MinitaskType
from civrealm.envs.freeciv_wrapper.tensor_wrapper import TensorWrapper
from civrealm.envs.freeciv_wrapper.utils import *
from civrealm.freeciv.utils.port_utils import Ports

# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings(
    "ignore", message=".*The obs returned by the .* method.*")


@pytest.fixture(params=MinitaskType.list())
def env_with_type(request):
    minitask_pattern = request.param
    env = gymnasium.make(
        "freeciv/FreecivTensorMinitask-v0",
        client_port=Ports.get(),
        minitask_pattern=minitask_pattern,
    )
    yield env, minitask_pattern
    env.close()


def test_minitask_tensor_env(env_with_type):
    # TODO: test other tasks, only buildcity and battle saves are supported now
    # if task_name not in ["buildcity", "battle"]:
    #     _, _ = env.reset()
    #     return

    env, minitask_pattern = env_with_type
    obs, _ = env.reset()
    unit_action_pos = np.where(obs["unit_action_type_mask"] == 1)
    idx = np.random.randint(len(unit_action_pos[0]))
    act_unit = {
        "actor_type": 1,
        "unit_id": unit_action_pos[0][idx],
        "unit_action_type": unit_action_pos[1][idx],
    }
    obs, reward, terminated, truncated, info = env.step(act_unit)
    if terminated or truncated:
        print("Early Win!")
        return

    city_action_pos = np.where(obs["city_action_type_mask"] == 1)
    if len(city_action_pos[0]) > 0:
        idx = np.random.randint(len(city_action_pos[0]))
        act_city = {
            "actor_type": 0,
            "city_id": city_action_pos[0][idx],
            "city_action_type": city_action_pos[1][idx],
        }
        obs, reward, terminated, truncated, info = env.step(act_city)
        if terminated or truncated:
            print("Early Win!")
            return

    gov_action_pos = np.where(obs["gov_action_type_mask"] == 1)
    action_type = np.random.choice(gov_action_pos[0])
    act_gov = {
        "actor_type": 2,
        "gov_action_type": action_type,
    }
    obs, reward, terminated, truncated, info = env.step(act_gov)
