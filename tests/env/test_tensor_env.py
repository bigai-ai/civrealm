import warnings

import gymnasium
import numpy as np
import pytest

from civrealm.configs import fc_args
from civrealm.envs.freeciv_tensor_env import FreecivTensorEnv
from civrealm.envs.freeciv_wrapper.utils import *
from civrealm.freeciv.utils.port_utils import Ports

# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings("ignore", message=".*The obs returned by the .* method.*")


@pytest.fixture
def env():
    fc_args["debug.load_game"] = "testcontroller_T169_2023-07-26-10_28"
    # fc_args['username']= 'testcontroller_T257_2023-08-07-14_04'

    env = FreecivTensorEnv(client_port=Ports.get())
    yield env
    env.close()


@pytest.fixture
def zero_start_env():
    fc_args["debug.load_game"] = ""

    env = FreecivTensorEnv(client_port=Ports.get())
    yield env
    env.close()


@pytest.fixture
def make_env():
    fc_args["debug.load_game"] = "testcontroller_T200_2023-07-31-01_51"
    # fc_args['username']= 'testcontroller_T257_2023-08-07-14_04'

    env = gymnasium.make("freeciv/FreecivTensor-v0", client_port=Ports.get())
    yield env
    env.close()


def test_tensor_env(env):
    obs, info = env.reset()
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

    tech_action_pos = np.where(obs["tech_action_type_mask"] == 1)
    action_type = np.random.choice(tech_action_pos[0])
    act_tech = {
        "actor_type": 3,
        "tech_action_type": action_type,
    }
    obs, reward, terminated, truncated, info = env.step(act_tech)


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
    if terminated or truncated:
        print("Early Win!")
        return

    city_action_pos = np.where(obs["city_action_type_mask"] == 1)
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

    city_action_pos = np.where(obs["city_action_type_mask"] == 1)
    idx = np.random.randint(len(city_action_pos[0]))
    act_end_turn = {
        "actor_type": 4,
    }
    obs, reward, terminated, truncated, info = env.step(act_end_turn)
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

    tech_action_pos = np.where(obs["tech_action_type_mask"] == 1)
    action_type = np.random.choice(tech_action_pos[0])
    act_tech = {
        "actor_type": 3,
        "tech_action_type": action_type,
    }
    obs, reward, terminated, truncated, info = env.step(act_tech)


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
    if terminated or truncated:
        print("Early Win!")
        return

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
    if terminated or truncated:
        print("Early Win!")
        return

    act_end_turn = {
        "actor_type": 4,
    }
    obs, reward, terminated, truncated, info = env.step(act_end_turn)

    tech_action_pos = np.where(obs["tech_action_type_mask"] == 1)
    action_type = np.random.choice(tech_action_pos[0])
    act_tech = {
        "actor_type": 3,
        "tech_action_type": action_type,
    }
    obs, reward, terminated, truncated, info = env.step(act_tech)
