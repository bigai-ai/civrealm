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

import numpy as np
import gymnasium
from gymnasium.core import Wrapper
from freeciv_gym.freeciv.utils.unit_improvement_const import UNIT_TYPES
from freeciv_gym.freeciv.map.map_const import TERRAIN_NAMES, EXTRA_NAMES
from freeciv_gym.freeciv.utils.language_agent_utility import (TILE_INFO_TEMPLATE, BLOCK_INFO_TEMPLATE,
                                                              DIR, action_mask, get_valid_actions)
from freeciv_gym.freeciv.players.player_const import DS_TXT
from freeciv_gym.freeciv.utils.utility import read_sub_arr_with_wrap


class LLMWrapper(Wrapper):

    def __init__(self, env, config):
        self.llm_config = config
        self._obs_initialized = False
        self._observation_space = None

        super().__init__(env)
        self.__env = env

    def reset(self, seed=None, options=None):
        obs, info = self.__env.reset()
        observation = self.get_llm_observation(obs, info)

        return observation, info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.__env.step(action)
        observation = self.get_llm_observation(obs, info)

        return observation, reward, terminated, truncated, info

    @property
    def observation_space(self):
        if self._obs_initialized:
            return self._observation_space
        else:
            return gymnasium.spaces.Discrete(1)

    def _obs_space(self, obs):
        obs_space = dict()
        for ctrl_type in obs:
            obs_space[ctrl_type] = gymnasium.spaces.Discrete(1)
        return gymnasium.spaces.Dict(obs_space)

    def get_llm_observation(self, obs, info):
        if not self._obs_initialized:
            self._observation_space = self._obs_space(obs)
            self._obs_initialized = True

        observation = dict()
        for ctrl_type in obs:
            observation[ctrl_type] = dict()
            actors_can_act = None
            if ctrl_type in info['available_actions']:
                actors_can_act = info['available_actions'][ctrl_type]

            if ctrl_type == 'unit':
                units = self.__env.civ_controller.unit_ctrl.units
                for unit_id in actors_can_act:
                    if units[unit_id]['activity'] != 0:
                        continue

                    x = obs[ctrl_type][unit_id]['x']
                    y = obs[ctrl_type][unit_id]['y']
                    utype = obs[ctrl_type][unit_id]['type_rule_name']
                    observation[ctrl_type][unit_id] = self.get_actor_info(x, y, info, ctrl_type, unit_id, utype)

            elif ctrl_type == 'city':
                for city_id in actors_can_act:
                    if obs[ctrl_type][city_id]['prod_process'] == 0:

                        x = obs[ctrl_type][city_id]['x']
                        y = obs[ctrl_type][city_id]['y']
                        observation[ctrl_type][city_id] = self.get_actor_info(x, y, info, ctrl_type, city_id)
                    else:
                        continue
            else:
                continue

        return observation

    def get_actor_info(self, x, y, info, ctrl_type, actor_id, utype=None):
        actor_info = dict()

        actor_name = None
        if ctrl_type == 'unit':
            actor_name = utype + ' ' + str(actor_id)
        elif ctrl_type == 'city':
            actor_name = ctrl_type + ' ' + str(actor_id)
        actor_info['name'] = actor_name

        available_actions = get_valid_actions(info, ctrl_type, actor_id)
        if not available_actions:
            return dict()
        else:
            if ctrl_type == 'unit':
                actor_info['available_actions'] = available_actions
            elif ctrl_type == 'city':
                actor_info['available_actions'] = action_mask(available_actions)

        actor_info['observations'] = dict()
        actor_info['observations']['minimap'] = self.get_mini_map_info(x, y, 0, 0, TILE_INFO_TEMPLATE)
        actor_info['observations']['upper_map'] = self.get_mini_map_info(x, y, 2, 2, BLOCK_INFO_TEMPLATE)

        return actor_info

    def get_mini_map_info(self, x, y, length_r, width_r, template):
        mini_map_info = dict()

        tile_id = 0
        map_state = self.civ_controller.map_ctrl.prop_state.get_state()
        for ptile in template:
            mini_map_info[ptile] = []
            pdir = DIR[tile_id]
            center_x = x + pdir[0] * (length_r * 2 + 1)
            center_y = y + pdir[1] * (width_r * 2 + 1)

            if not self.civ_controller.map_ctrl.is_out_of_map(center_x, center_y):
                """ consider map_const.TF_WRAPX == 1 """
                start_x = center_x - length_r
                end_x = center_x + length_r + 1
                start_y = center_y - width_r
                end_y = center_y + width_r + 1

                status_arr = read_sub_arr_with_wrap(map_state['status'], start_x, end_x, start_y, end_y)
                terrain_arr = read_sub_arr_with_wrap(map_state['terrain'], start_x, end_x, start_y, end_y)
                extras_arr = read_sub_arr_with_wrap(map_state['extras'], start_x, end_x, start_y, end_y)
                unit_arr = read_sub_arr_with_wrap(map_state['unit'], start_x, end_x, start_y, end_y)
                unit_owner_arr = read_sub_arr_with_wrap(map_state['unit_owner'], start_x, end_x, start_y, end_y)
                city_owner_arr = read_sub_arr_with_wrap(map_state['city_owner'], start_x, end_x, start_y, end_y)

                unexplored_tiles_num = len(list(status_arr[status_arr == 0]))
                if unexplored_tiles_num > 0:
                    status_str = str(unexplored_tiles_num) + ' ' + 'tiles unexplored'
                    mini_map_info[ptile].append(status_str)

                for terrain_id, terrain in enumerate(TERRAIN_NAMES):
                    terrains_num = len(list(terrain_arr[terrain_arr == terrain_id]))
                    if terrains_num > 0:
                        terrain_str = str(terrains_num) + ' ' + terrain
                        mini_map_info[ptile].append(terrain_str)

                for extra_id, extra in enumerate(EXTRA_NAMES):
                    extras_of_id = extras_arr[:, :, extra_id]
                    extras_num = len(list(extras_of_id[extras_of_id != 0]))
                    if extras_num > 0:
                        extra_str = str(extras_num) + ' ' + extra
                        mini_map_info[ptile].append(extra_str)

                for unit_id, unit in enumerate(UNIT_TYPES):
                    units_of_id = unit_arr[:, :, unit_id]
                    units_num = np.sum(units_of_id)
                    if units_num > 0:
                        unit_str = str(int(units_num)) + ' ' + unit
                        mini_map_info[ptile].append(unit_str)

                owner_set = []
                unit_owner_str = 'unit owners are:'
                for unit_owner in list(unit_owner_arr[unit_owner_arr != 255]):
                    if unit_owner in owner_set:
                        continue

                    if unit_owner == self.civ_controller.player_ctrl.my_player_id:
                        unit_owner_str += ' myself player_' + str(int(unit_owner))
                    else:
                        ds_of_owner = self.civ_controller.dipl_ctrl.diplstates[unit_owner]
                        unit_owner_str += ' ' + DS_TXT[ds_of_owner] + ' player_' + str(int(unit_owner))
                    mini_map_info[ptile].append(unit_owner_str)
                    owner_set.append(unit_owner)

                owner_set = []
                for city_owner in list(city_owner_arr[city_owner_arr != 255]):
                    if city_owner in owner_set:
                        continue

                    if city_owner == self.civ_controller.player_ctrl.my_player_id:
                        city_owner_str = '1 city of myself player_' + str(int(city_owner))
                    else:
                        ds_of_owner = self.civ_controller.dipl_ctrl.diplstates[city_owner]
                        city_owner_str = '1 city of a ' + DS_TXT[ds_of_owner] + ' player_' + str(int(city_owner))
                    mini_map_info[ptile].append(city_owner_str)
                    owner_set.append(city_owner)

            tile_id += 1
        return mini_map_info


