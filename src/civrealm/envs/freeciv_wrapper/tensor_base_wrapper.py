import numpy as np

from civrealm.envs import FreecivBaseEnv
from civrealm.envs.freeciv_wrapper.config import default_tensor_config

from .core import Wrapper
from .utils import onehotifier_maker


class TensorBase(Wrapper):
    """
    A basic wrapper that deals with config loading and entity id recording, 
    required by all tensor-related wrappers.


    Parameters
    ----------
    env: FreecivBaseEnv
    config: dict
        tensor env configuration

    Attributes
    ---------
    config: dict
        A dict that specifies all configurations related to tensor wrapper.
    my_player_id: int
        My player id.
    unit_ids: list
        A sorted list of my unit ids.
    city_ids: list
        A sorted list of my city ids.
    others_unit_ids: list
        A sorted list of others unit ids.
    others_city_ids: list
        A sorted list of others city ids.
    dipl_ids : list
        A list of others player ids.
    units : dict
        ruleset information about units.
    unit_types :list
        A list of all unit types.
    unit_costs : list
        A list of int indicating unit costs.
    improvements : dict
        Ruleset information about city improvements.
    impr_costs :list
        A list of int indicating city improvements costs.

    """

    def __init__(self, env: FreecivBaseEnv, config: dict = default_tensor_config):
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
        """
        Use city, unit and dipl information in observation to update ids.
        """
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
        """
        Update config using ruleset information at the start of the turn.
        """
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
