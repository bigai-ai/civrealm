# Copyright (C) 2023  The CivRealm project
#
# This program is free software: you can redistribute it and/or modify it
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
from gymnasium.core import Wrapper
from civrealm.freeciv.utils.fc_types import ACTIVITY_IDLE, ACTIVITY_FORTIFIED, ACTIVITY_SENTRY, ACTIVITY_FORTIFYING
from civrealm.freeciv.utils.unit_improvement_const import UNIT_TYPES
from civrealm.freeciv.map.map_const import TERRAIN_NAMES, EXTRA_NAMES
from civrealm.freeciv.utils.language_agent_utility import (TILE_INFO_TEMPLATE, BLOCK_INFO_TEMPLATE,
                                                           DIR, action_mask, get_valid_actions)
from civrealm.freeciv.players.player_const import DS_TXT
from civrealm.freeciv.utils.utility import read_sub_arr_with_wrap
from civrealm.freeciv.utils.freeciv_logging import fc_logger


class LLMWrapper(Wrapper):

    def __init__(self, env):
        super().__init__(env)
        self.__env = env

    def reset(self, seed=None, options=None, **kwargs):
        if 'minitask_pattern' in kwargs:
            observation, info = self.__env.reset(minitask_pattern=kwargs['minitask_pattern'])
        else:
            observation, info = self.__env.reset()

        info['llm_info'] = self.get_llm_info(observation, info)
        info['my_player_id'] = self.civ_controller.player_ctrl.my_player_id
        return observation, info

    def step(self, action):
        observation, reward, terminated, truncated, info = self.__env.step(action)
        info['llm_info'] = self.get_llm_info(observation, info)
        info['my_player_id'] = self.civ_controller.player_ctrl.my_player_id
        return observation, reward, terminated, truncated, info

    def get_llm_info(self, obs, info):
        current_turn = info['turn']

        llm_info = dict()
        for ctrl_type, actors_can_act in info['available_actions'].items():
            llm_info[ctrl_type] = dict()

            if ctrl_type == 'unit':
                units = self.civ_controller.unit_ctrl.units
                for unit_id in actors_can_act:
                    if (units[unit_id]['type'] == 1 and units[unit_id]['activity'] not in
                            [ACTIVITY_IDLE, ACTIVITY_FORTIFIED, ACTIVITY_SENTRY, ACTIVITY_FORTIFYING]):
                        continue

                    x = obs[ctrl_type][unit_id]['x']
                    y = obs[ctrl_type][unit_id]['y']
                    utype = obs[ctrl_type][unit_id]['type_rule_name']

                    unit_dict = self.get_actor_info(x, y, info, ctrl_type, unit_id, utype)
                    if unit_dict:
                        llm_info[ctrl_type][unit_id] = unit_dict

            elif ctrl_type == 'city':
                for city_id in actors_can_act:
                    # The following two conditions are used to check if 1.  the city is just built or is building
                    # coinage, and 2. the city has just built a unit or an improvement last turn and there are some
                    # production points left in stock.
                    if (obs[ctrl_type][city_id]['prod_process'] == 0 or
                            current_turn == obs[ctrl_type][city_id]['turn_last_built'] + 1):
                        x = obs[ctrl_type][city_id]['x']
                        y = obs[ctrl_type][city_id]['y']

                        city_dict = self.get_actor_info(x, y, info, ctrl_type, city_id)
                        if city_dict:
                            llm_info[ctrl_type][city_id] = city_dict
                    else:
                        continue
            else:
                continue

        return llm_info

    def get_actor_info(self, x, y, info, ctrl_type, actor_id, utype=None):
        actor_info = dict()

        actor_name = None
        if ctrl_type == 'unit':
            actor_name = utype + ' ' + str(actor_id)
        elif ctrl_type == 'city':
            actor_name = ctrl_type + ' ' + str(actor_id)
        actor_info['name'] = actor_name

        available_actions = get_valid_actions(info, ctrl_type, actor_id)
        if not available_actions or (len(available_actions) == 1 and available_actions[0] == 'keep_activity'):
            return dict()
        else:
            if ctrl_type == 'unit':
                actor_info['available_actions'] = available_actions
            elif ctrl_type == 'city':
                actor_info['available_actions'] = action_mask(available_actions)

        actor_info['observations'] = dict()
        actor_info['observations']['minimap'] = self.get_mini_map_info(x, y, 0, 0, TILE_INFO_TEMPLATE)
        actor_info['observations']['upper_map'] = self.get_mini_map_info(x, y, 2, 2, BLOCK_INFO_TEMPLATE)

        fc_logger.debug(f'actor observations: {actor_info}')

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

                unit_owners = list(unit_owner_arr[unit_owner_arr != 255])
                if len(unit_owners) != 0:
                    owner_set = []
                    unit_owner_str = 'unit owners are:'
                    for unit_owner in unit_owners:
                        if unit_owner in owner_set:
                            continue

                        if unit_owner == self.civ_controller.player_ctrl.my_player_id:
                            unit_owner_str += ' myself player_' + str(int(unit_owner))
                        else:
                            ds_of_owner = self.civ_controller.dipl_ctrl.diplstates[unit_owner]
                            unit_owner_str += ' ' + DS_TXT[ds_of_owner] + ' player_' + str(int(unit_owner))
                        owner_set.append(unit_owner)
                    mini_map_info[ptile].append(unit_owner_str)

                city_owners = list(city_owner_arr[city_owner_arr != 255])
                for city_owner in self.civ_controller.player_ctrl.players:
                    owner_num = city_owners.count(city_owner)
                    if owner_num == 0:
                        continue

                    if city_owner == self.civ_controller.player_ctrl.my_player_id:
                        city_owner_str = str(owner_num) + ' cities of myself player_' + str(int(city_owner))
                    else:
                        ds_of_owner = self.civ_controller.dipl_ctrl.diplstates[city_owner]
                        city_owner_str = (str(owner_num) + ' cities of a ' + DS_TXT[ds_of_owner] +
                                          ' player_' + str(int(city_owner)))
                    mini_map_info[ptile].append(city_owner_str)

            tile_id += 1
        return mini_map_info
