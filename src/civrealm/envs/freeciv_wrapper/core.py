from functools import wraps
from inspect import signature
from typing import Literal, Sequence, Type

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

    def __init__(
        self,
        methods: Sequence[
            Literal[
                "observation", "reward", "terminated", "truncated", "info", "action"
            ]
        ],
    ):
        if len(set(methods) - set(self.method_args)) != 0:
            raise ValueError(
                f"`methods' should be a list of strings within {self.method_args+['action']}, but got {methods}."
            )
        self.override_action = "action" in methods
        self.overrides = methods
        self.func_signatures = {}

    def _step_wrapper(self, wrapped_step):
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
            for method_name in overrides:
                result[method_name] = getattr(self, method_name)(
                    **{arg: result[arg] for arg in func_signatures[method_name]}
                )
            return tuple(result[name] for name in result_names)

        return step

    def _reset_wrapper(self, wrapped_reset):
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

    def __call__(self, cls: Type[gymnasium.Wrapper]):
        if not issubclass(cls, gymnasium.Wrapper):
            raise TypeError(f"`{cls}' must be a subclass of `gymnasium.Wrapper'")
        for func_name in self.overrides:
            if not hasattr(cls, func_name):
                raise NotImplementedError(
                    f"{cls} hasn't implemented `{func_name}' yet!"
                )
            sigs = list(signature(getattr(cls, func_name)).parameters.keys())
            sigs.remove("self")
            if len(set(sigs) - set(self.method_args)) != 0:
                raise ValueError(
                    f"{cls} method `{func_name}' should only use\
argument names within {self.method_args}, but got {sigs}"
                )

            if "wrapped_action" in sigs:
                raise ValueError(
                    f"{cls} method `{func_name}' uses 'wrapped_action'\
, but `action' is not overriden!"
                )

            self.func_signatures[func_name] = sigs
        cls.step = self._step_wrapper(cls.step)
        cls.reset = self._reset_wrapper(cls.reset)
        return cls
