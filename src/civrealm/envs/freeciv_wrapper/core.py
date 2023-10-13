import gymnasium


class Wrapper(gymnasium.Wrapper):
    def reset(self, *, seed=None, options=None, **kwargs):
        return self.env.reset(seed=seed, options=options, **kwargs)


class ObservationWrapper(gymnasium.ObservationWrapper):
    def reset(self, *, seed=None, options=None, **kwargs):
        obs, info = self.env.reset(seed=seed, options=options, **kwargs)
        return self.observation(obs), info
