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

import numpy
from collections import Mapping
from typing import Sequence, Any, Optional, Dict
from gymnasium.core import Wrapper
from freeciv_gym.envs.freeciv_base_env import FreecivBaseEnv

from freeciv_gym.configs import fc_args
from freeciv_gym.envs.freeciv_wrapper.utils import *


class FreecivTensorEnv(Wrapper):
    """Freeciv gym environment with code actions"""

    def __init__(
        self, client_port: int = fc_args["client_port"], config: dict = default_config
    ):
        base_env = FreecivBaseEnv(client_port)
        self.config = config

        super().__init__(base_env)

    def reset(
        self, *, seed: Optional[int] = None, options: Optional[dict[str, Any]] = None
    ):
        """Modifies the :attr:`env` after calling :meth:`reset`, returning a modified observation using :meth:`self.observation`."""
        obs, info = self.env.reset(seed=seed, options=options)
        self.unit_ids = []
        self.city_ids = []
        return self.observation(obs), info

    def step(self, action):
        observation, reward, terminated, truncated, info = self.env.step(action)
        return self.observation(observation), reward, terminated, truncated, info

    def observation(self, observation):
        self.update_sequence_ids(observation)
        return self.handcraft_obs(observation)

    def update_sequence_ids(self, observation):
        self.unit_ids = sorted(list(observation["unit"].keys()))
        self.city_ids = sorted(list(observation["city"].keys()))

    def handcraft_obs(self, obs):
        # put others' units/cities into obs['others_unit/city']
        # TODO: check owner id equal to my id
        import pdb; pdb.set_trace()
        for key in list(obs.keys()):
            if key not in self.config["filter_observation"]:
                obs.pop(key)

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
        obs["others_player"] = {}
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
        obs["others_player"] = update(
            obs["others_player"], self.civ_controller.player_ctrl.players
        )

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

        recursive_print(obs)
        import pdb; pdb.set_trace()
        return obs

        # TODO: construct other_units x,y,city_radius_sq, buy_cost, shield_stock, before_change_shields, disbanded_shields, caravan_shields, last_turns_shield_surplus
