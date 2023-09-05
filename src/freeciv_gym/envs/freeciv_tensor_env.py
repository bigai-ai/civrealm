# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from typing import Any, Optional
from gymnasium.core import Wrapper
from freeciv_gym.envs.freeciv_base_env import FreecivBaseEnv

from freeciv_gym.configs import fc_args
from freeciv_gym.envs.freeciv_wrapper.utils import *


class FreecivTensorEnv(Wrapper):
    """Freeciv gym environment with Tensor actions"""

    def __init__(
        self, client_port: int = fc_args["client_port"], config: dict = default_config
    ):
        base_env = FreecivBaseEnv(client_port)
        self.config = config
        self.obs_initialized = False
        self._observation_space: Optional[spaces.Dict] = None

        super().__init__(base_env)

    def reset(
        self, *, seed: Optional[int] = None, options: Optional[dict[str, Any]] = None
    ):
        """Modifies the :attr:`env` after calling :meth:`reset`, returning a modified observation using :meth:`self.observation`."""
        obs, info = self.env.reset(seed=seed, options=options)
        self.unit_ids = []
        self.city_ids = []
        self.turn = 0
        self.reset_mask()
        self.update_sequence_ids(obs)
        mask = self.get_mask(obs, info)
        obs = self.observation(obs)
        obs = update(obs, mask)
        return obs, info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.unwrapped.step(
            self.action(action)
        )
        self.update_sequence_ids(obs)
        mask = self.get_mask(obs, info, action)
        obs = self.observation(obs)
        obs = update(obs, mask)
        return obs, reward, terminated, truncated, info

    def observation(self, observation):
        observation = deepcopy(observation)
        obs= self.filter_map_obs(observation)
        obs = self.stack_obs(obs)
        obs = self.resize_obs(obs)
        if not self.obs_initialized:
            self._observation_space = self._infer_obs_space(obs)
            self.obs_initialized = True
        return obs

    @property
    def action_space(self):
        return spaces.Dict(
            {
                "actor_type": spaces.Discrete(
                    4
                ),  # actor_type_dim = 4; 0 for city, 1 for unit, 2 for gov, 3 for turn done
                "city_id": spaces.Discrete(self.config["resize"]["city"]),
                "city_action_type": spaces.Discrete(207),
                "unit_id": spaces.Discrete(self.config["resize"]["unit"]),
                "unit_action_type": spaces.Discrete(122),
                "gov_action_type": spaces.Discrete(6),
            }
        )

    @property
    def observation_space(self):
        if self.obs_initialized:
            return self._observation_space
        else:
            raise Exception(
                "Observation space not initiliazed yet. \
Please call observation_space AFTER observation being returned."
            )

    def action(self, action):
        actor_type_dict = ['turn done','unit','city','gov']
        actor_type = action["actor_type"]
        actor_name = actor_type_dict[actor_type]
        if actor_type == 0:
            return None
        elif actor_type == 1:
            id = self.unit_ids[action["unit_id"]]
            action_index = action["unit_action_type"]
            action_list = sorted(
                list(self.action_list[actor_name][id].keys())
            )
            return ("unit", id, action_list[action_index])
        elif actor_type == 2:
            id = self.city_ids[action["city_id"]]
            action_index = action["city_action_type"]
            action_list = sorted(
                list(self.action_list[actor_name][id].keys())
            )
            return ("city", id, action_list[action_index])
        elif actor_type == 3:
            id = 0
            action_index = action["gov_action_type"]
            action_list = sorted(
                list(self.action_list[actor_name][id].keys())
            )
            return ("gov", id, action_list[action_index])
        else:
            raise ValueError(
                "'actor_type' field in action dict should be an int between 0 and 3, but got {actor_type}."
            )

    def _infer_obs_space(self, observation) -> spaces.Dict:
        return spaces.Dict(
            [
                (key, spaces.Box(low=0, high=1, shape=space.shape, dtype=np.int32))
                for key, space in observation.items()
            ]
        )

    def update_sequence_ids(self, observation):
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

    def stack_obs(self, obs):
        for key, val in obs.items():
            #'map'
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

    def resize_obs(self, obs):
        for key, size in self.config["resize"].items():
            obs[key] = resize_data(obs[key], size)
        return obs

    def filter_map_obs(self, obs):
        # TODO: check owner id equal to my id
        for key, val in obs['dipl'].items():
            update(obs['player'][key],val)

        for key in list(obs.keys()):
            if key not in self.config["filter_observation"]:
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
        # TODO: construct other_units x,y,city_radius_sq, buy_cost, shield_stock, before_change_shields, disbanded_shields, caravan_shields, last_turns_shield_surplus
        return obs

    def get_mask(self, observation, info, action=None):
        if info["turn"] != self.turn:
            self.reset_mask()
        self.action_list = info["available_actions"]
        self.turn = info["turn"]
        self.update_mask(observation, info, action)
        return {
            "units_mask": self.units_mask.astype(np.int32),
            "cities_mask": self.cities_mask.astype(np.int32),
            "other_units_mask": self.other_units_mask.astype(np.int32),
            "other_cities_mask": self.other_cities_mask.astype(np.int32),
            "other_players_mask": self.other_players_mask.astype(np.int32),
            "actor_type_mask": self.actor_type_mask.astype(np.int32),
            "city_id_mask": self.city_id_mask.astype(np.int32),
            "city_action_type_mask": self.city_action_type_mask.astype(np.int32),
            "unit_id_mask": self.unit_id_mask.astype(np.int32),
            "unit_action_type_mask": self.unit_action_type_mask.astype(np.int32),
            "gov_action_type_mask": self.gov_action_type_mask.astype(np.int32),
        }

    def reset_mask(self):
        sizes = self.config["resize"]
        # Actor Type Mask
        self.actor_type_mask = np.ones(4)

        # Units/Cities/Players and others Masks
        self.units_mask = np.ones(sizes["unit"])[..., np.newaxis]
        self.cities_mask = np.ones(sizes["city"])[..., np.newaxis]
        self.other_units_mask = np.ones(sizes["others_unit"])[..., np.newaxis]
        self.other_cities_mask = np.ones(sizes["others_city"])[..., np.newaxis]
        self.other_players_mask = np.ones(sizes["others_player"])[..., np.newaxis]

        # Units/Cities Masks same as others
        self.unit_id_mask = self.units_mask
        self.city_id_mask = self.cities_mask

        # Action type mask
        self.city_action_type_mask = np.ones((sizes["city"], 207))
        self.unit_action_type_mask = np.ones((sizes["unit"], 122))
        self.gov_action_type_mask = np.ones(6)

    def update_mask(self, observation, info, action=None):
        if action:
            self.mask_from_action(action)
        self.mask_from_obs(observation)
        self.mask_from_info(info)

    def mask_from_action(self, action):
        actor_type = action['actor_type']
        if actor_type == 0:
            return None
        elif actor_type == 1:
            self.unit_action_type_mask[action['unit_id'], action['unit_action_type']] *= 0
        elif actor_type == 2:
            self.city_action_type_mask[action['city_id'], action['city_action_type']] *= 0
        elif actor_type == 3:
            self.gov_action_type_mask[action['gov_action_type']] *= 0
        else:
            raise ValueError(
                f"'actor_type' field in action dict should be an int between 0 and 3, but got {actor_type}."
            )

    def mask_from_obs(self, observation):
        self.units_mask[len(self.unit_ids) : :, :] *= 0
        self.cities_mask[len(self.city_ids) : :, :] *= 0
        for pos,id in enumerate(self.unit_ids[:self.config['resize']['unit']]):
            unit = observation['unit'][id]
            if unit["moves_left"] == 0:
                self.units_mask[pos] *= 0
                self.unit_action_type_mask[pos] *= 0
        self.unit_id_mask = self.units_mask
        self.city_id_mask = self.cities_mask
        self.other_units_mask[len(self.others_unit_ids) : :, :] *= 0
        self.other_cities_mask[len(self.others_city_ids) : :, :] *= 0

    def mask_from_info(self, info):
        other_players_num = len(info["available_actions"]["player"].keys())
        self.other_players_mask[other_players_num::, :] = 1

        if units := info["available_actions"].get("unit", False):
            for i, unit_id in enumerate(self.unit_ids[:self.config['resize']['unit']]):
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
            for i, city_id in enumerate(self.city_ids[:self.config['resize']['city']]):
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
