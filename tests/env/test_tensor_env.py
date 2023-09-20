import pytest
import random
import numpy as np
import time

from freeciv_gym.envs.freeciv_tensor_env import FreecivTensorEnv
from freeciv_gym.envs.freeciv_wrapper.utils import *
from freeciv_gym.freeciv.utils.port_list import DEV_PORT_LIST
import gymnasium

import warnings

# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings("ignore", message=".*The obs returned by the .* method.*")

from freeciv_gym.configs import fc_args

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
    fc_args["debug.load_game"] = "testcontroller_T200_2023-07-31-01_51"
    # fc_args['username']= 'testcontroller_T257_2023-08-07-14_04'
    env = FreecivTensorEnv(client_port=get_client_port())

    yield env
    env.close()

@pytest.fixture
def zero_start_env():
    fc_args["debug.load_game"] = ""
    env = FreecivTensorEnv(client_port=get_client_port())

    yield env
    env.close()

@pytest.fixture
def make_env():
    fc_args["debug.load_game"] = "testcontroller_T200_2023-07-31-01_51"
    # fc_args['username']= 'testcontroller_T257_2023-08-07-14_04'
    env = gymnasium.make('freeciv/FreecivTensor-v0', client_port=get_client_port())

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
    obs, reward, terminated, truncated, info = env.step(act_unit)

    city_action_pos = np.where(obs["city_action_type_mask"] == 1)
    idx = np.random.randint(len(city_action_pos[0]))
    act_city = {
        "actor_type": 0,
        "city_id": city_action_pos[0][idx],
        "city_action_type": city_action_pos[1][idx],
    }
    obs, reward, terminated, truncated, info = env.step(act_city)

    gov_action_pos = np.where(obs["gov_action_type_mask"] == 1)
    action_type = np.random.choice(gov_action_pos[0])
    act_gov = {
        "actor_type": 2,
        "gov_action_type": action_type,
    }
    obs, reward, terminated, truncated, info = env.step(act_gov)

def test_tensor_make_env(make_env):
    env = make_env
    obs, _ = env.reset()
    unit_action_pos = np.where(obs["unit_action_type_mask"] == 1)
    idx = np.random.randint(len(unit_action_pos[0]))
    act_unit = {
        "actor_type": 1,
        "unit_id": unit_action_pos[0][idx],
        "unit_action_type": unit_action_pos[1][idx],
    }
    obs, reward, terminated, truncated, info = env.step(act_unit)

    city_action_pos = np.where(obs["city_action_type_mask"] == 1)
    idx = np.random.randint(len(city_action_pos[0]))
    act_city = {
        "actor_type": 0,
        "city_id": city_action_pos[0][idx],
        "city_action_type": city_action_pos[1][idx],
    }
    obs, reward, terminated, truncated, info = env.step(act_city)

    city_action_pos = np.where(obs["city_action_type_mask"] == 1)
    idx = np.random.randint(len(city_action_pos[0]))
    act_end_turn = {
        "actor_type": 3,
        "city_id": city_action_pos[0][idx],
        "city_action_type": city_action_pos[1][idx],
    }
    obs, reward, terminated, truncated, info = env.step(act_end_turn)

    gov_action_pos = np.where(obs["gov_action_type_mask"] == 1)
    action_type = np.random.choice(gov_action_pos[0])
    act_gov = {
        "actor_type": 2,
        "gov_action_type": action_type,
    }
    obs, reward, terminated, truncated, info = env.step(act_gov)

def test_tensor_zero_start_env(zero_start_env):
    env = zero_start_env
    obs, _ = env.reset()
    unit_action_pos = np.where(obs["unit_action_type_mask"] == 1)
    idx = np.random.randint(len(unit_action_pos[0]))
    act_unit = {
        "actor_type": 1,
        "unit_id": unit_action_pos[0][idx],
        "unit_action_type": unit_action_pos[1][idx],
    }
    obs, reward, terminated, truncated, info = env.step(act_unit)

    # city_action_pos = np.where(obs["city_action_type_mask"] == 1)
    # idx = np.random.randint(len(city_action_pos[0]))
    # act_city = {
    #     "actor_type": 2,
    #     "city_id": city_action_pos[0][idx],
    #     "city_action_type": city_action_pos[1][idx],
    # }
    # obs, reward, terminated, truncated, info = env.step(act_city)

    gov_action_pos = np.where(obs["gov_action_type_mask"] == 1)
    action_type = np.random.choice(gov_action_pos[0])
    act_gov = {
        "actor_type": 2,
        "gov_action_type": action_type,
    }
    obs, reward, terminated, truncated, info = env.step(act_gov)

    act_end_turn = {
        "actor_type": 3,
    }
    obs, reward, terminated, truncated, info = env.step(act_end_turn)

    import pdb; pdb.set_trace()
