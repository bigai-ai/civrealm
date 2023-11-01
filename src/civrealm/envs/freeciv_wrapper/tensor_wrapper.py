from civrealm.envs.freeciv_wrapper.config import default_tensor_config

from .action_wrapper import TensorAction
from .core import Wrapper
from .observation_wrapper import CacheLastObs, TensorObservation


class TensorWrapper(Wrapper):
    def __init__(self, env, config=default_tensor_config):
        env = CacheLastObs(
            TensorObservation(
                TensorAction(TensorBase(env), config=config), config=config
            )
        )
        self.config = config
        super().__init__(env)


class TensorBase(Wrapper):
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
            for player in sorted(observation.get("dipl",{}).keys())
            if player != self.my_player_id
        ]

    def reset(self, *args, **kwargs):
        obs, info = self.env.reset(*args, **kwargs)
        self.my_player_id = self.unwrapped.civ_controller.player_ctrl.my_player_id
        self.update_sequence_ids(obs)
        return obs, info

    def step(self, *args, **kwargs):
        obs, reward, terminated, truncated, info = self.env.step(*args, **kwargs)
        self.update_sequence_ids(obs)
        return obs, reward, terminated, truncated, info
