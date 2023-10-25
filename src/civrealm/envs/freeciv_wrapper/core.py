from functools import wraps
from inspect import signature
from typing import Sequence

import gymnasium


class Wrapper(gymnasium.Wrapper):
    def reset(self, *, seed=None, options=None, **kwargs):
        return self.env.reset(seed=seed, options=options, **kwargs)


class wrapper_override:
    result_names = [
        "observation",
        "reward",
        "terminated",
        "truncated",
        "info",
    ]
    method_args = result_names + ["action", "wrapped_action"]

    def __init__(self, methods: Sequence[str]):
        assert len(set(methods) - set(self.method_args)) == 0
        self.override_action = "action" in methods
        self.overrides = set(methods)
        self.func_signatures = {}

    def step_wrapper(self, wrapped_step):
        override_action = self.override_action
        overrides = self.overrides
        result_names = self.result_names
        func_signatures = self.func_signatures

        @wraps(wrapped_step)
        def step(self, action):
            wrapped_action = self.action(action) if override_action else action
            result = dict(list(zip(result_names, wrapped_step(self, wrapped_action))))
            result["wrapped_action"] = wrapped_action
            result["action"] = action
            if "observation" in overrides:
                result["observation"] = self.observation(
                    **{arg: result[arg] for arg in func_signatures["observation"]}
                )
            if "reward" in overrides:
                result["reward"] = self.reward(
                    **{arg: result[arg] for arg in func_signatures["reward"]}
                )
            if "terminated" in overrides:
                result["terminated"] = self.terminated(
                    **{arg: result[arg] for arg in func_signatures["terminated"]}
                )
            if "truncated" in overrides:
                result["truncated"] = self.truncated(
                    **{arg: result[arg] for arg in func_signatures["truncated"]}
                )
            if "info" in overrides:
                result["info"] = self.info(
                    **{arg: result[arg] for arg in func_signatures["info"]}
                )
            return tuple(result[name] for name in result_names)

        return step

    def reset_wrapper(self, wrapped_reset):
        overrides = self.overrides
        func_signatures = self.func_signatures

        @wraps(wrapped_reset)
        def reset(self, *args, **kwargs):
            obs, info = wrapped_reset(self, *args, **kwargs)
            result = {"observation": obs, "info": info}
            if "observation" in overrides:
                obs = self.observation(
                    **{
                        arg: result[arg]
                        for arg in func_signatures["observation"]
                        if arg in result
                    }
                )
            if "info" in overrides:
                info = self.info(
                    **{
                        arg: result[arg]
                        for arg in func_signatures["info"]
                        if arg in result
                    }
                )
            return obs, info

        return reset

    def __call__(self, cls):
        assert issubclass(cls, gymnasium.Wrapper)
        for func_name in self.overrides:
            assert hasattr(cls, func_name)
            sigs = list(signature(getattr(cls, func_name)).parameters.keys())
            sigs.remove("self")
            assert len(set() - set(self.method_args)) == 0
            if "wrapped_action" in sigs:
                assert self.override_action

            self.func_signatures[func_name] = sigs
        cls.step = self.step_wrapper(cls.step)
        cls.reset = self.reset_wrapper(cls.reset)
        return cls
