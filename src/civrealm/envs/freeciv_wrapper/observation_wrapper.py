from collections import OrderedDict
from copy import deepcopy
from functools import reduce

import numpy as np
from gymnasium import spaces

from civrealm.configs import fc_args

from .core import ObservationWrapper, Wrapper
from .utils import add_shape, resize_data, update

tensor_debug = fc_args["debug.tensor_debug"]


class TensorObservation(ObservationWrapper):
    mutable_fields = ["city", "unit", "others_city", "others_unit", "others_player"]
    immutable_fields = ["map", "rules", "player", "tech", "gov"]

    def __init__(self, env, config):
        self.obs_initialized = False
        self.observation_config = config
        self.obs_layout = {}
        self.others_player_ids = []
        super().__init__(env)

    def observation(self, observation):
        # in case of gameover, return None as observation
        if len(observation["player"]) == 0:
            return None

        observation = deepcopy(observation)
        obs_dict = self._handle_dict(observation)
        obs = self._embed_immutable(deepcopy(obs_dict))
        obs = self._embed_mutable(obs)

        if not self.obs_initialized:
            self.observation_space = self._infer_obs_space(obs)
            self.obs_initialized = True
        if tensor_debug:
            self._check_obs_layout(obs)
        return obs

    def _handle_dict(self, obs):
        obs["city"] = obs.get("city", {})
        obs["unit"] = obs.get("unit", {})

        # TODO: This should be the base env's reponsibility
        # Add info to city and unit from civcontroller
        update(obs["city"], self.civ_controller.city_ctrl.cities)
        update(obs["unit"], self.civ_controller.unit_ctrl.units)
        # update player info with dipl
        update(obs["player"], obs.get("dipl", {}))

        # remove unused fields and keep mask if given
        obs = {
            k: v
            for k, v in obs.items()
            if k in self.observation_config["filter_observation"] or k.endswith("mask")
        }

        # Add others fields and initialize
        my_player_id = self.get_wrapper_attr("my_player_id")

        obs["others_unit"] = {}
        obs["others_city"] = {}

        for field in ["unit", "city"]:
            for key, val in list(obs[field].items()):
                if val["owner"] != my_player_id:
                    # delete others' entity from unit and city
                    obs["others_" + field][key] = obs[field].pop(key)

        obs["others_player"] = {
            key: obs["player"].pop(key)
            for key in list(obs["player"].keys())
            if key != my_player_id
        }
        obs["player"] = obs["player"][my_player_id]

        # Initialize build_cost with 0 for now
        obs["rules"]["build_cost"] = 0

        mutable_fields = [field for field in obs.keys() if field in self.mutable_fields]
        immutable_fields = [
            field for field in obs.keys() if field in self.immutable_fields
        ]

        ops = self.observation_config["obs_ops"]

        # Handle immutable
        # delete unused keywords and transform useful keywords
        def apply_ops(field):
            for k, val in list(obs[field].items()):
                if k in list(ops[field].keys()):
                    obs[field][k] = ops[field][k](val)
                else:
                    obs[field].pop(k)

        for field in immutable_fields:
            apply_ops(field)

        # Handle mutable
        # delete unused keywords and transform useful keywords
        def apply_ops_mutable(field):
            for entity_id, entity in list(obs[field].items()):
                for k, val in list(entity.items()):
                    if k in list(ops[field].keys()):
                        entity[k] = ops[field][k](val)
                    else:
                        entity.pop(k)

        for field in mutable_fields:
            apply_ops_mutable(field)

        self.others_player_ids = sorted(obs["others_player"].keys())

        return obs

    def _embed_immutable(self, obs):
        immutable = {
            field: obs[field] for field in obs if field in self.immutable_fields
        }

        if not self.obs_initialized:
            for field, field_dict in immutable.items():
                self.obs_layout[field] = OrderedDict(
                    [(k, field_dict[k].shape) for k in sorted(list(field_dict.keys()))]
                )

        for field, field_dict in immutable.items():
            # check field layout is correct
            if tensor_debug:
                assert self.obs_layout[field] == {
                    k: v.shape for k, v in field_dict.items()
                }

            obs[field] = np.concatenate(
                [field_dict[k] for k in sorted(list(field_dict.keys()))], axis=-1
            )
        return obs

    def _embed_mutable(self, obs):
        mutable = {field: obs[field] for field in obs if field in self.mutable_fields}
        mutable_layout = self.observation_config["obs_mutable_layout"]

        if not self.obs_initialized:
            for field, entity_dict in mutable.items():
                layout = mutable_layout[field]
                self.obs_layout[field] = OrderedDict(
                    [(key, layout[key]) for key in sorted(layout)]
                )

        for field, entity_dict in mutable.items():
            # for empty field, fill with zero
            if len(entity_dict) == 0:
                mutable[field] = np.zeros(
                    [
                        self.observation_config["resize"][field],
                        *reduce(add_shape, self.obs_layout[field].values()),
                    ]
                )
                continue
            if tensor_debug:
                # check entity layout is correct
                assert all(
                    self.obs_layout[field] == {k: v.shape for k, v in entity.items()}
                    for entity in entity_dict.values()
                )
            # combine every entity's properties into an array along the last axis
            entity_dict = {
                id: np.concatenate([entity[k] for k in sorted(entity.keys())], axis=-1)
                for id, entity in entity_dict.items()
            }
            # combine all entities in a field into an array along the first axis
            mutable[field] = np.stack(
                [entity_dict[id] for id in getattr(self, field + "_ids")], axis=0
            )

        # resize to maximum entity shape
        for field in mutable:
            size = self.observation_config["resize"][field]
            mutable[field] = resize_data(mutable[field], size)

        update(obs, mutable)
        return obs

    def _infer_obs_space(self, observation) -> spaces.Dict:
        return spaces.Dict(
            [
                (key, spaces.Box(low=0, high=1000, shape=space.shape, dtype=np.int32))
                for key, space in observation.items()
            ]
        )

    def _check_obs_layout(self, obs):
        for field, val in self.obs_layout.items():
            shape = reduce(add_shape, val.values())
            assert shape[-1] == obs[field].shape[-1]


class CacheLastObs(Wrapper):
    def __init__(self, env):
        self.cached_last_obs = None
        super().__init__(env)

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)

        if terminated or truncated:
            obs = self.cached_last_obs
            info = {} if info is None else info
            return obs, reward, terminated, truncated, info

        self.cached_last_obs = deepcopy(obs)
        return obs, reward, terminated, truncated, info
