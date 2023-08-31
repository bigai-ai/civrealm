import pytest
import time
import random

from freeciv_gym.envs.freeciv_wrapper import FilterObservation, get_keys
from freeciv_gym.freeciv.utils.port_list import DEV_PORT_LIST
import gymnasium

import warnings

# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings("ignore", message=".*The obs returned by the .* method.*")


@pytest.fixture
def env(worker_id):
    print(f"worker_id:{worker_id}")
    env = gymnasium.make("freeciv/FreecivBase-v0", client_port=random.choice(DEV_PORT_LIST))
    yield env
    env.close()
    time.sleep(10)


config = {
    "map": {
        "status": ['onehot', 3],
        "terrain": ['onehot', 14],
        "extras": ['default'],
        "output": ['onehot', 6],
        "tile_owner": ['default'],
        "city_owner": ['default'],
        "unit": ['default'],
        "unit_owner": ['default']
    }
}

onehot_config = {
    "map": {
        "status": ((78, 52), 3),
        "terrain": ((78, 52), 14),
        "output": ('onehot', 6),
        "tile_owner": ('default'),
        "city_owner": ('default'),
        "unit": ('default'),
        "unit_owner": ('default')
    }
}


@pytest.mark.parametrize("filter_out", [True, False])
def test_FilterNestedWrapper(env, filter_out):
    obs_space = env.observation_space
    wrapped = FilterObservation(
        env, get_keys(config), filter_out
    )
    obs, info = wrapped.reset()
    if filter_out:
        assert ('map' not in obs)
    else:
        assert (['map'] == list(obs.keys()))
        assert (set(config['map'].keys()) == set(obs['map'].keys()))
