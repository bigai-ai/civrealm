# Copyright (C) 2023  The Freeciv-gym project
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
from freeciv_gym.envs.freeciv_base_env import FreecivBaseEnv
from freeciv_gym.freeciv.utils.unit_improvement_const import UNIT_TYPES
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.map.map_const import TERRAIN_NAMES, EXTRA_NAMES
from freeciv_gym.freeciv.utils.language_agent_utility import (TILE_INFO_TEMPLATE, BLOCK_INFO_TEMPLATE,
                                                              DIR, action_mask, get_valid_actions)
from freeciv_gym.freeciv.players.player_const import DS_TXT
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.freeciv.utils.utility import read_sub_arr_with_wrap


class FreecivLLMEnv(FreecivBaseEnv):
    """ Freeciv gym environment with code actions """

    def __init__(self, client_port: int = fc_args['client_port']):
        super().__init__(client_port=client_port)

    def get_actor_info(self, info, ctrl_type, actor_id, ptile, utype=None):
        actor_info = dict()

        # Populate name
        actor_name = None
        if ctrl_type == 'unit':
            actor_name = UNIT_TYPES[utype] + ' ' + str(actor_id)
        elif ctrl_type == 'city':
            actor_name = 'City' + ' ' + str(actor_id)
        actor_info['name'] = actor_name

        # Populate available actions
        available_actions = get_valid_actions(info, ctrl_type, actor_id)
        if not available_actions:
            return dict()
        else:
            if ctrl_type == 'unit':
                actor_info['available_actions'] = available_actions
            elif ctrl_type == 'city':
                actor_info['available_actions'] = action_mask(available_actions)

        # Populate observations
        actor_info['observations'] = dict()
        actor_info['observations']['minimap'] = self.get_mini_map_info(ptile)
        actor_info['observations']['upper_map'] = self.get_upper_map_info(ptile)

        return actor_info

    def get_mini_map_info(self, ptile):
        x = ptile['x']
        y = ptile['y']
        mini_map_info = dict()

        tile_id = 0
        for ptile in TILE_INFO_TEMPLATE:
            mini_map_info[ptile] = []
            pdir = DIR[tile_id]
            dx = pdir[0]
            dy = pdir[1]

            map_state = self.civ_controller.map_ctrl.prop_state.get_state()
            (length, width) = map_state['status'].shape
            if not self.civ_controller.map_ctrl.is_out_of_map(x + dx, y + dy):
                new_x = x + dx
                new_y = y + dy
                if x + dx < 0:
                    new_x = length + x + dx
                if x + dx > (length - 1):
                    new_x = (x + dx) % (length - 1)

                if map_state['status'][new_x, new_y] == 0:
                    mini_map_info[ptile].append('unexplored')

                if map_state['terrain'][new_x, new_y] != 255:
                    terrain_id = map_state['terrain'][new_x, new_y]
                    terrain_str = TERRAIN_NAMES[terrain_id]
                    mini_map_info[ptile].append(terrain_str)

                for extra_id, extra_name in enumerate(EXTRA_NAMES):
                    if map_state['extras'][new_x, new_y, extra_id]:
                        mini_map_info[ptile].append(extra_name)

                for unit_id, unit_name in enumerate(UNIT_TYPES):
                    if map_state['unit'][new_x, new_y, unit_id]:
                        units_num = map_state['unit'][new_x, new_y, unit_id]
                        mini_map_info[ptile].append(str(int(units_num)) + ' ' + unit_name)

                if map_state['unit_owner'][new_x, new_y] != 255:
                    unit_owner = map_state['unit_owner'][new_x, new_y]
                    if unit_owner == self.civ_controller.player_ctrl.my_player_id:
                        units_dsp = 'Units belong to myself player_' + str(int(unit_owner))
                    else:
                        ds_of_units = self.civ_controller.dipl_ctrl.diplstates[unit_owner]
                        units_dsp = ('Units belong to a ' + DS_TXT[ds_of_units] + ' player_' + str(int(unit_owner)))
                    mini_map_info[ptile].append(units_dsp)

                if map_state['city_owner'][new_x, new_y] != 255:
                    city_owner = map_state['city_owner'][new_x, new_y]
                    if city_owner == self.civ_controller.player_ctrl.my_player_id:
                        city_dsp = '1 city belongs to myself player_' + str(city_owner)
                    else:
                        ds_of_city = self.civ_controller.dipl_ctrl.diplstates[city_owner]
                        city_dsp = '1 city belongs to a ' + DS_TXT[ds_of_city] + ' player_' + str(city_owner)
                    mini_map_info[ptile].append(city_dsp)

            tile_id += 1
        return mini_map_info

    def get_llm_info(self, info):
        llm_info = dict()
        for ctrl_type, actors_can_act in info['available_actions'].items():
            llm_info[ctrl_type] = dict()
            if ctrl_type == 'unit':
                units = self.civ_controller.unit_ctrl.units
                for unit_id in actors_can_act:
                    if units[unit_id]['activity'] != 0:
                        continue
                    
                    ptile = self.civ_controller.map_ctrl.index_to_tile(units[unit_id]['tile'])
                    utype = units[unit_id]['type']
                    llm_info[ctrl_type][unit_id] = self.get_actor_info(info, ctrl_type, unit_id, ptile, utype)

            elif ctrl_type == 'city':
                cities = self.civ_controller.city_ctrl.cities
                for city_id in actors_can_act:
                    if (self.civ_controller.turn_manager.turn == 1 or
                            self.civ_controller.turn_manager.turn == cities[city_id]['turn_last_built'] + 1):
                        ptile = self.civ_controller.map_ctrl.index_to_tile(cities[city_id]['tile'])
                        llm_info[ctrl_type][city_id] = self.get_actor_info(info, ctrl_type, city_id, ptile)
                    else:
                        continue
            else:
                continue

        return llm_info

    def step(self, action):
        import time
        start_time = time.time()

        self.civ_controller.perform_action(action)
        info, observation = self._get_info_and_observation()

        llm_info = self.get_llm_info(info)
        info['llm_info'] = llm_info

        reward = self._get_reward()
        terminated = self._get_terminated()
        truncated = self._get_truncated()

        available_actions = info['available_actions']
        self._record_action(available_actions, action)

        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time > 15:
            fc_logger.debug('Running too slow.')
            assert False

        return observation, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        self.civ_controller.init_network()
        info, observation = self._get_info_and_observation()

        llm_info = self.get_llm_info(info)
        info['llm_info'] = llm_info

        return observation, info

    def get_upper_map_info(self, ptile):
        length_r = width_r = 2
        x = ptile['x']
        y = ptile['y']
        upper_map_info = dict()

        tile_id = 0
        map_state = self.civ_controller.map_ctrl.prop_state.get_state()
        for ptile in BLOCK_INFO_TEMPLATE:
            upper_map_info[ptile] = []
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
                    upper_map_info[ptile].append(status_str)

                for terrain_id, terrain in enumerate(TERRAIN_NAMES):
                    terrains_num = len(list(terrain_arr[terrain_arr == terrain_id]))
                    if terrains_num > 0:
                        terrain_str = str(terrains_num) + ' ' + terrain
                        upper_map_info[ptile].append(terrain_str)

                for extra_id, extra in enumerate(EXTRA_NAMES):
                    extras_of_id = extras_arr[:, :, extra_id]
                    extras_num = len(list(extras_of_id[extras_of_id != 0]))
                    if extras_num > 0:
                        extra_str = str(extras_num) + ' ' + extra
                        upper_map_info[ptile].append(extra_str)

                for unit_id, unit in enumerate(UNIT_TYPES):
                    units_of_id = unit_arr[:, :, unit_id]
                    units_num = np.sum(units_of_id)
                    if units_num > 0:
                        unit_str = str(int(units_num)) + ' ' + unit
                        upper_map_info[ptile].append(unit_str)

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
                    upper_map_info[ptile].append(unit_owner_str)
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
                    upper_map_info[ptile].append(city_owner_str)
                    owner_set.append(city_owner)

            tile_id += 1
        return upper_map_info




