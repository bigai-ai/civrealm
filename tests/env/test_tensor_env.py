import pytest
import random
import numpy as np

from freeciv_gym.envs.freeciv_tensor_env import FreecivTensorEnv
from freeciv_gym.freeciv.utils.port_list import DEV_PORT_LIST

import warnings

# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings("ignore", message=".*The obs returned by the .* method.*")

from freeciv_gym.configs import fc_args


@pytest.fixture
def env():
    fc_args["debug.load_game"] = "testcontroller_T200_2023-07-31-01_51"
    # fc_args['username']= 'testcontroller_T257_2023-08-07-14_04'
    env = FreecivTensorEnv(random.choice(DEV_PORT_LIST))

    yield env
    env.close()


def test_tensor_env(env):
    obs, _ = env.reset()
    unit_action_pos = np.where(obs["unit_action_type_mask"] == 1)
    idx = np.random.randint(len(unit_action_pos[0]))
    act_unit = {
        "actor_type": 1,
        "unit_id": unit_action_pos[0][idx],
        "unit_action_type": unit_action_pos[1][idx],
    }
    obs, reward, terminated, truncated, info =env.step(act_unit)

    city_action_pos = np.where(obs["city_action_type_mask"] == 1)
    idx = np.random.randint(len(city_action_pos[0]))
    act_city = {
        "actor_type": 2,
        "city_id": city_action_pos[0][idx],
        "city_action_type": city_action_pos[1][idx],
    }
    obs, reward, terminated, truncated, info =env.step(act_city)

    gov_action_pos = np.where(obs["gov_action_type_mask"] == 1)
    action_type = np.random.choice(gov_action_pos[0])
    act_gov = {
        "actor_type": 3,
        "gov_action_type": action_type,
    }
    obs, reward, terminated, truncated, info =env.step(act_gov)
