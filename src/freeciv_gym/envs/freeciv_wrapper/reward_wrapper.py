from gymnasium.core import Wrapper
from gymnasium.wrappers import flatten_observation

from freeciv_gym.envs.freeciv_wrapper.utils import *


class RewardWrapper(Wrapper):
    def __init__(self, env):
        Wrapper.__init__(self, env)

    def step(self, action):
        observation, reward, terminated, truncated, info = self.env.step(action)
        return (
            observation,
            self.reward(
                observation=observation,
                reward=reward,
                terminated=terminated,
                truncated=truncated,
                info=info,
                action=action,
            ),
            terminated,
            truncated,
            info,
        )

    def reward(
        self,
        observation=None,
        reward=None,
        terminated=None,
        truncated=None,
        info=None,
        action=None,
    ):
        raise NotImplementedError


class PenalizeTurnDoneReward(RewardWrapper):
    def __init__(self, env, penalty=-1):
        self._penalty_reward = penalty
        RewardWrapper.__init__(self, env)

    def reward(self, reward, action, **kwargs):
        if action == None and reward == 0:
            # if last action is `turn done' and delta score is 0 
            # use penalty reward
            return self._penalty_reward
        else:
            return reward
