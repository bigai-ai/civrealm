import logging
from gym.envs.registration import register

logger = logging.getLogger(__name__)

register(
    id='Freeciv-v0',
    entry_point='gym_freeciv_web.envs:FreecivEnv',
    # timestep_limit=1000,
    # reward_threshold=1.0,
    # nondeterministic = True,
)
