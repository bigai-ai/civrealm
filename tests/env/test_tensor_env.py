import pytest
import random

from freeciv_gym.envs.freeciv_tensor_env import  *
from freeciv_gym.freeciv.utils.port_list import DEV_PORT_LIST

import warnings

# FIXME: This is a hack to suppress the warning about the gymnasium spaces. Currently Gymnasium does not support hierarchical actions.
warnings.filterwarnings("ignore", message=".*The obs returned by the .* method.*")

from freeciv_gym.configs import fc_args

@pytest.fixture
def env():
    fc_args['debug.load_game']= "testcontroller_T200_2023-07-31-01_51"
    # fc_args['username']= 'testcontroller_T257_2023-08-07-14_04'
    env = FreecivTensorEnv(random.choice(DEV_PORT_LIST))

    yield env
    env.close()

def test_tensor_env(env):
    obs, info = env.reset()
