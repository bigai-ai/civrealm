from typing import Any, Optional

from gymnasium.core import Env, Wrapper

from freeciv_gym.envs.freeciv_wrapper.utils import *


class TensorWrapper(Wrapper):
    def __init__(self, env: Env, config: dict = default_tensor_config):
        self.tensor_config = config
        self._obs_initialized = False
        self._observation_space: Optional[spaces.Dict] = None
        self._seed = None
        self._embarkable_units = {}

        super().__init__(env)
        self.__env = env

    def reset(
        self, *, seed: Optional[int] = None, options: Optional[dict[str, Any]] = None, **kwargs
    ):
        if seed is None:
            seed = self._seed
        obs, info = self.__env.reset(seed=seed, options=options, **kwargs)
        self.unit_ids = []
        self.city_ids = []
        self.turn = 0
        self._reset_mask()
        self._update_sequence_ids(obs)
        info = self._handle_embark_info(info)
        self.mask = self._get_mask(obs, info)
        obs = self.observation(obs)
        return obs, info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.__env.step(self.action(action))
        self._update_sequence_ids(obs)
        info = self._handle_embark_info(info)
        self.mask = self._get_mask(obs, info, action)
        obs = self.observation(obs)
        return obs, reward, terminated, truncated, info

    def observation(self, observation):
        observation = deepcopy(observation)
        obs = self._filter_map_obs(observation)
        obs = self._stack_obs(obs)
        obs = self._resize_obs(obs)
        obs = update(obs, self.mask)
        if not self._obs_initialized:
            self._observation_space = self._infer_obs_space(obs)
            self._obs_initialized = True
        return obs

    @property
    def action_space(self):
        return spaces.Dict(
            {
                "actor_type": spaces.Discrete(
                    4
                ),  # actor_type_dim = 4; 0 for city, 1 for unit, 2 for gov, 3 for turn done
                "city_id": spaces.Discrete(self.tensor_config["resize"]["city"]),
                "city_action_type": spaces.Discrete(207),
                "unit_id": spaces.Discrete(self.tensor_config["resize"]["unit"]),
                "unit_action_type": spaces.Discrete(122 + 8),
                "gov_action_type": spaces.Discrete(6),
            }
        )

    @property
    def observation_space(self):
        if self._obs_initialized:
            return self._observation_space
        else:
            return spaces.Discrete(1)

    def action(self, action):
        action = deref_dict(action)
        actor_type_list = ["turn done", "unit", "city", "gov"]
        actor_type = action["actor_type"]
        actor_name = actor_type_list[actor_type]
        if actor_type == 0:
            return None
        elif actor_type == 1:
            id_pos, action_index = action["unit_id"], action["unit_action_type"]
            assert (
                self.unit_action_type_mask[id_pos, action_index] == 1
            ), f"unit action of id pos {id_pos}, action type index {action_index} is masked"
            id = self.unit_ids[action["unit_id"]]
            action_name = sorted(list(self.action_list[actor_name][id].keys()))[
                action_index
            ]
            return self._handle_embark_action(("unit", id, action_name))
        elif actor_type == 2:
            id_pos, action_index = action["city_id"], action["city_action_type"]
            assert (
                self.city_action_type_mask[id_pos, action_index] == 1
            ), f"city action of id pos {id_pos}, action type index {action_index} is masked"
            id = self.city_ids[action["city_id"]]
            action_name = sorted(list(self.action_list[actor_name][id].keys()))[
                action_index
            ]
            return ("city", id, action_name)
        elif actor_type == 3:
            id = 0
            action_index = action["gov_action_type"]
            assert (
                self.gov_action_type_mask[action_index] == 1
            ), f"gov action of action type index {action_index} is masked"
            action_list = sorted(list(self.action_list[actor_name][id].keys()))
            return ("gov", id, action_list[action_index])
        else:
            raise ValueError(
                "'actor_type' field in action dict should be an int between 0 and 3, but got {actor_type}."
            )

    def seed(self, seed):
        self._seed = seed

    def _infer_obs_space(self, observation) -> spaces.Dict:
        return spaces.Dict(
            [
                (key, spaces.Box(low=0, high=1000, shape=space.shape, dtype=np.int32))
                for key, space in observation.items()
            ]
        )

    def _update_sequence_ids(self, observation):
        # TODO: check owner id equal to my id
        self.unit_ids = sorted(
            list(
                k
                for k in observation["unit"].keys()
                if observation["unit"][k]["owner"] == 0
            )
        )
        self.others_unit_ids = sorted(
            list(
                k
                for k in observation["unit"].keys()
                if observation["unit"][k]["owner"] != 0
            )
        )
        self.city_ids = sorted(
            list(
                k
                for k in observation["city"].keys()
                if observation["city"][k]["owner"] == 0
            )
        )
        self.others_city_ids = sorted(
            list(
                k
                for k in observation["city"].keys()
                if observation["city"][k]["owner"] != 0
            )
        )

    def _stack_obs(self, obs):
        for key, val in obs.items():
            if len(val) == 0:
                continue
            if isinstance(next(iter(val.values())), dict):
                for id, subval in val.items():
                    # terrain
                    val[id] = np.concatenate(
                        [subval[k] for k in sorted(subval.keys())], axis=-1
                    )
                obs[key] = np.stack(
                    [val[id] for id in getattr(self, key + "_ids")], axis=0
                )
            else:
                obs[key] = np.concatenate(
                    [val[k] for k in sorted(list(val.keys()))], axis=-1
                )
        return obs

    def _resize_obs(self, obs):
        for key, val in obs.items():
            if len(val) == 0:
                obs[key] = np.zeros(
                    [self.tensor_config["resize"][key], obs_possible_size[key]]
                )
        for key, size in self.tensor_config["resize"].items():
            obs[key] = resize_data(obs[key], size)
        return obs

    def _filter_map_obs(self, obs):
        # TODO: check owner id equal to my id
        for key, val in obs["dipl"].items():
            update(obs["player"][key], val)

        for key in list(obs.keys()):
            if key not in self.tensor_config["filter_observation"]:
                obs.pop(key)

        obs["others_player"] = {
            key: val for key, val in obs["player"].items() if key != 0
        }
        obs["player"] = obs["player"][0]

        # Handle map and players
        for key, val in list(obs["map"].items()):
            if key in list(map_ops.keys()):
                obs["map"][key] = map_ops[key](val)
            else:
                obs["map"].pop(key)
        for key, val in list(obs["player"].items()):
            if key in list(player_ops.keys()):
                obs["player"][key] = player_ops[key](val)
            else:
                obs["player"].pop(key)
        obs["rules"]["build_cost"] = 0
        for key, val in list(obs["rules"].items()):
            if key in list(rules_ops.keys()):
                obs["rules"][key] = rules_ops[key](val)
            else:
                obs["rules"].pop(key)

        obs["others_unit"] = {}
        obs["others_city"] = {}

        for key, val in list(obs["unit"].items()):
            if val["owner"] != 0:
                obs["others_unit"][key] = obs["unit"].pop(key)
        for key, val in list(obs["city"].items()):
            if val["owner"] != 0:
                obs["others_city"][key] = obs["city"].pop(key)
        others_city = {
            k: v
            for (k, v) in self.civ_controller.city_ctrl.cities.items()
            if v["owner"] != 0
        }
        others_unit = {
            k: v
            for (k, v) in self.civ_controller.unit_ctrl.units.items()
            if v["owner"] != 0
        }

        # TODO: should be base env's responsibility to fill in others'unit fields
        obs["others_city"] = update(obs["others_city"], others_city)
        obs["others_unit"] = update(obs["others_unit"], others_unit)
        # obs["others_player"] = update(
        #     obs["others_player"], self.civ_controller.player_ctrl.players
        # )

        # All information should be complete after this point
        for key, val in list(obs["others_unit"].items()):
            for k, v in list(val.items()):
                if k in list(others_unit_ops.keys()):
                    val[k] = others_unit_ops[k](v)
                else:
                    val.pop(k)
        for key, val in list(obs["others_city"].items()):
            for k, v in list(val.items()):
                if k in list(others_city_ops.keys()):
                    val[k] = others_city_ops[k](v)
                else:
                    val.pop(k)
        for key, val in list(obs["others_player"].items()):
            for k, v in list(val.items()):
                if k in list(others_player_ops.keys()):
                    val[k] = others_player_ops[k](v)
                else:
                    val.pop(k)
        self.others_player_ids = sorted(obs["others_player"].keys())

        for key, val in list(obs["unit"].items()):
            for k, v in list(val.items()):
                if k in list(unit_ops.keys()):
                    val[k] = unit_ops[k](v)
                else:
                    val.pop(k)

        for key, val in list(obs["city"].items()):
            for k, v in list(val.items()):
                if k in list(city_ops.keys()):
                    val[k] = city_ops[k](v)
                else:
                    val.pop(k)
        # TODO: construct others_units x,y,city_radius_sq, buy_cost, shield_stock, before_change_shields, disbanded_shields, caravan_shields, last_turns_shield_surplus
        return obs

    def _get_mask(self, observation, info, action=None):
        if info["turn"] != self.turn:
            self._reset_mask()
        self.action_list = info["available_actions"]
        self.turn = info["turn"]
        self._update_mask(observation, info, action)
        return {
            "unit_mask": self.unit_mask.astype(np.int32),
            "city_mask": self.city_mask.astype(np.int32),
            "others_unit_mask": self.others_unit_mask.astype(np.int32),
            "others_city_mask": self.others_city_mask.astype(np.int32),
            "others_player_mask": self.others_player_mask.astype(np.int32),
            "actor_type_mask": self.actor_type_mask.astype(np.int32),
            "city_id_mask": self.city_id_mask.astype(np.int32),
            "city_action_type_mask": self.city_action_type_mask.astype(np.int32),
            "unit_id_mask": self.unit_id_mask.astype(np.int32),
            "unit_action_type_mask": self.unit_action_type_mask.astype(np.int32),
            "gov_action_type_mask": self.gov_action_type_mask.astype(np.int32),
        }

    def _reset_mask(self):
        sizes = self.tensor_config["resize"]
        # Actor Type Mask
        self.actor_type_mask = np.ones(4)

        # Units/Cities/Players and others Masks
        self.unit_mask = np.ones(sizes["unit"])[..., np.newaxis]
        self.city_mask = np.ones(sizes["city"])[..., np.newaxis]
        self.others_unit_mask = np.ones(sizes["others_unit"])[..., np.newaxis]
        self.others_city_mask = np.ones(sizes["others_city"])[..., np.newaxis]
        self.others_player_mask = np.ones(sizes["others_player"])[..., np.newaxis]

        # Units/Cities Masks same as others
        self.unit_id_mask = self.unit_mask
        self.city_id_mask = self.city_mask

        # Action type mask
        self.city_action_type_mask = np.ones((sizes["city"], 207))
        self.unit_action_type_mask = np.ones((sizes["unit"], 122 + 8))
        self.gov_action_type_mask = np.ones(6)

    def _update_mask(self, observation, info, action=None):
        if action:
            self._mask_from_action(action)
        self._mask_from_obs(observation)
        self._mask_from_info(info)

    def _mask_from_action(self, action):
        actor_type = action["actor_type"]
        if actor_type == 0:
            return None
        elif actor_type == 1:
            self.unit_action_type_mask[
                action["unit_id"], action["unit_action_type"]
            ] *= 0
        elif actor_type == 2:
            self.city_action_type_mask[
                action["city_id"], action["city_action_type"]
            ] *= 0
        elif actor_type == 3:
            # self.gov_action_type_mask[action["gov_action_type"]] *= 0
            self.gov_action_type_mask *= 0
            self.actor_type_mask[3] *= 0
        else:
            raise ValueError(
                f"'actor_type' field in action dict should be an int between 0 and 3, but got {actor_type}."
            )

    def _mask_from_obs(self, observation):
        self.unit_mask[len(self.unit_ids) : :, :] *= 0
        self.city_mask[len(self.city_ids) : :, :] *= 0
        self.unit_action_type_mask[len(self.unit_ids) : :, :] *= 0
        self.city_action_type_mask[len(self.city_ids) : :, :] *= 0
        for pos, id in enumerate(self.unit_ids[: self.tensor_config["resize"]["unit"]]):
            unit = observation["unit"][id]
            if unit["moves_left"] == 0:
                self.unit_mask[pos] *= 0
                self.unit_action_type_mask[pos] *= 0
        self.unit_id_mask = self.unit_mask
        self.city_id_mask = self.city_mask
        self.others_unit_mask[len(self.others_unit_ids) : :, :] *= 0
        self.others_city_mask[len(self.others_city_ids) : :, :] *= 0

    def _mask_from_info(self, info):
        others_player_num = len(info["available_actions"]["player"].keys())
        self.others_player_mask[others_player_num::, :] = 0

        if units := info["available_actions"].get("unit", False):
            for i, unit_id in enumerate(self.unit_ids[: self.tensor_config["resize"]["unit"]]):
                if actions := units.get(unit_id, False):
                    for id, act_name in enumerate(sorted(list(actions.keys()))):
                        self.unit_action_type_mask[i, id] *= int(actions[act_name])
                else:
                    self.unit_action_type_mask[i] *= 0
                self.unit_id_mask[i] = int(any(self.unit_action_type_mask[i]))
        else:
            self.unit_action_type_mask *= 0
            self.unit_id_mask *= 0
        self.actor_type_mask[1] = int(any(self.unit_id_mask))

        if citys := info["available_actions"].get("city", False):
            for i, city_id in enumerate(self.city_ids[: self.tensor_config["resize"]["city"]]):
                if actions := citys.get(city_id, False):
                    for id, act_name in enumerate(sorted(list(actions.keys()))):
                        self.city_action_type_mask[i, id] *= int(actions[act_name])
                else:
                    self.city_action_type_mask[i] *= 0
                self.city_id_mask[i] = int(any(self.city_action_type_mask[i]))
        else:
            self.city_action_type_mask *= 0
            self.city_id_mask *= 0
        self.actor_type_mask[2] = int(any(self.city_id_mask))

        if gov := info["available_actions"].get("gov", False):
            for id, act_name in enumerate(sorted(list(gov[0].keys()))):
                self.gov_action_type_mask[id] *= int(gov[0][act_name])
        else:
            self.gov_action_type_mask *= 0
        self.actor_type_mask[3] = int(any(self.gov_action_type_mask))

    def _handle_embark_info(self, info):
        self._embarkable_units = {}
        if unit_actions := info["available_actions"].get(["unit"], False):
            for id, actions in unit_actions.items():
                for action in list(actions.keys()):
                    if action[:6] == "embark":
                        args = action.split("_")
                        if len(args == 3):
                            [target_id,dir] = map(int, args[1::])
                            actions[f"embark_{dir}"] = True
                            if unit_dir := (id, dir) not in self._embarkable_units:
                                self._embarkable_units[unit_dir] = [target_id]
                            else:
                                self._embarkable_units[unit_dir] += [target_id]
                            actions.pop(action)
                        else:
                            dir = int( action.split("_")[-1])
                            actions[f"embark_{dir}"] = True

                for embark_action in ["embark_" + f"{i}" for i in range(8)]:
                    if embark_action not in actions:
                        actions[embark_action] = False
        return info

    def _handle_embark_action(self, action):
        if action[-1][:6] != "embark":
            return action
        elif len(self._embarkable_units) == 0 :
            return action
        assert action[0] == "unit"
        id = action[1]
        dir = int(action[-1].split("_")[-1])
        target_id = sorted(self._embarkable_units[(id, dir)])[0]
        action_type_name = f"embark_{dir}_{target_id}"
        return ("unit", id, action)
