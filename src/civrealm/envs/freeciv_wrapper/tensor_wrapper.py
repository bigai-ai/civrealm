import numpy as np

from civrealm.envs.freeciv_wrapper.config import default_tensor_config

from .action_wrapper import TensorAction
from .core import Wrapper
from .observation_wrapper import CacheLastObs, TensorObservation
from .utils import onehotifier_maker


class TensorWrapper(Wrapper):
    def __init__(self, env, config=default_tensor_config):
        env = CacheLastObs(
            TensorObservation(TensorAction(TensorBase(env, config=config)))
        )
        self.config = config
        super().__init__(env)


class TensorBase(Wrapper):
    def __init__(self, env, config=default_tensor_config):
        self.config = config
        self.my_player_id = -1

        # mutable ids
        self.unit_ids = []
        self.city_ids = []
        self.others_unit_ids = []
        self.others_city_ids = []
        self.dipl_ids = []

        # ruleset
        self.units = {}
        self.unit_types = []
        self.unit_costs = []
        self.improvements = {}
        self.impr_costs = []

        super().__init__(env)

    def update_sequence_ids(self, observation):
        self.unit_ids = sorted(
            list(
                k
                for k in observation.get("unit", {}).keys()
                if observation["unit"][k]["owner"] == self.my_player_id
            )
        )
        self.others_unit_ids = sorted(
            list(
                k
                for k in observation.get("unit", {}).keys()
                if observation["unit"][k]["owner"] != self.my_player_id
            )
        )
        self.city_ids = sorted(
            list(
                k
                for k in observation.get("city", {}).keys()
                if observation["city"][k]["owner"] == self.my_player_id
            )
        )
        self.others_city_ids = sorted(
            list(
                k
                for k in observation.get("city", {}).keys()
                if observation["city"][k]["owner"] != self.my_player_id
            )
        )
        self.dipl_ids = [
            player
            for player in sorted(observation.get("dipl", {}).keys())
            if player != self.my_player_id
        ]

    def update_config(self):
        self.units = self.unwrapped.civ_controller.rule_ctrl.unit_types
        self.unit_types = [self.units[i]["name"] for i in range(len(self.units))]
        self.unit_costs = [self.units[i]["build_cost"] for i in range(len(self.units))]
        self.improvements = self.unwrapped.civ_controller.rule_ctrl.improvements
        self.impr_costs = [
            self.improvements[i]["build_cost"] for i in range(len(self.improvements))
        ]
        self.config["obs_ops"]["unit"]["type_rule_name"] = onehotifier_maker(
            self.unit_types
        )
        self.config["obs_ops"]["rules"]["build_cost"] = lambda _: np.array(
            self.unit_costs + self.impr_costs
        )

    def reset(self, *args, **kwargs):
        obs, info = self.env.reset(*args, **kwargs)
        self.my_player_id = self.unwrapped.civ_controller.player_ctrl.my_player_id

        self.update_config()
        self.update_sequence_ids(obs)
        return obs, info

    def step(self, *args, **kwargs):
        obs, reward, terminated, truncated, info = self.env.step(*args, **kwargs)
        self.update_sequence_ids(obs)
        return obs, reward, terminated, truncated, info
