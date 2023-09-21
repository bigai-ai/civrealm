import gymnasium as gym


class Wrapper(gym.Wrapper):
    def reset(self, *, seed=None, options=None, **kwargs):
        return self.env.reset(seed=seed, options=options, **kwargs)
