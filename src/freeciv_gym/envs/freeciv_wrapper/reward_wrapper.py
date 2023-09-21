from gymnasium.core import Wrapper


class RewardWrapper(Wrapper):
    def __init__(self, env):
        Wrapper.__init__(self, env)

    def reset(self,**kwargs):
        return self.env.reset(**kwargs)

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
    def __init__(self, env, penalty: float = -1):
        self._penalty_reward = penalty
        RewardWrapper.__init__(self, env)

    def reward(self, reward, action, **kwargs):
        if action == None and reward == 0:
            # if last action is `turn done' and delta score is 0
            # use penalty reward
            return self._penalty_reward
        else:
            return reward


class MinitaskDenseReward(RewardWrapper):
    def __init__(self, env, replacement=True):
        self._replacement = replacement
        self._last_score = 0
        RewardWrapper.__init__(self, env)

    def reward(self, reward, info, **kwargs):
        score = info["minitask"]["mini_score"]
        delta_score = score - self._last_score
        self._last_score = score
        assert isinstance(score, int) or isinstance(score, float)
        if self._replacement:
            return delta_score
        else:
            return reward + delta_score


class MinitaskDelayedReward(RewardWrapper):
    def __init__(self, env, success_reward=1, replacement=True):
        self._replacement = replacement
        self._success_reward = success_reward
        RewardWrapper.__init__(self, env)

    def reward(self, reward, info, **kwargs):
        success = info["minitask"]["success"]
        score = int(success) * self._success_reward
        assert isinstance(success, int) or isinstance(success, bool)
        if self._replacement:
            return score
        else:
            return reward + score
