from .core import Wrapper, wrapper_override


@wrapper_override(["reward"])
class PenalizeConsecutiveTurnDoneReward(Wrapper):
    """A reward wrapper that penalizes the 'turn done' action if the delta score is 0."""

    def __init__(self, env, penalty: float = -1):
        self._penalty_reward = penalty
        self.last_action = None
        super().__init__(env)

    def reward(self, reward, action):
        if self.last_action is None and action is None and reward == 0:
            # if last action is `turn done' and delta score is 0
            # use penalty reward
            return self._penalty_reward
        self.last_action = action
        return reward


@wrapper_override(["reward"])
class PenalizeStep(Wrapper):
    def __init__(self, env):
        self.actions_in_turn = 0
        super().__init__(env)

    def reward(self, reward, action):
        if action is None:
            self.actions_in_turn = 0
            return reward
        self.actions_in_turn += 1
        return reward-1*int(self.actions_in_turn>20)


@wrapper_override(["reward"])
class MinitaskDenseReward(Wrapper):
    """A reward wrapper that provides dense rewards based on the delta score in a minitask."""

    def __init__(self, env, replacement=True):
        self._replacement = replacement
        self._last_score = 0
        super().__init__(env)

    def reward(self, reward, info):
        score = info["minitask"]["mini_score"]
        delta_score = score - self._last_score
        self._last_score = score
        assert isinstance(score, (int, float))
        if self._replacement:
            return delta_score
        return reward + delta_score


@wrapper_override(["reward"])
class MinitaskDelayedReward(Wrapper):
    """A reward wrapper that provides delayed rewards based on the success of a minitask."""

    def __init__(self, env, success_reward=1, replacement=True):
        self._replacement = replacement
        self._success_reward = success_reward
        super().__init__(env)

    def reward(self, reward, info):
        success = info["minitask"]["success"] > 0
        score = int(success) * self._success_reward
        if self._replacement:
            return score
        return reward + score
