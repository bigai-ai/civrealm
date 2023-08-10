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

import random
import numpy as np
from freeciv_gym.agents.base_agent import BaseAgent
from freeciv_gym.agents.controller_agent import ControllerAgent
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.map.map_const import TERRAIN_NAMES, EXTRA_NAMES
from freeciv_gym.freeciv.utils.type_const import UNIT_TYPES
import copy

RADIUS = 2
TILE_INFO_TEMPLATE = {
            'current_tile': [],
            'tile_north_1': [],
            'tile_south_1': [],
            'tile_east_1': [],
            'tile_west_1': [],
            'tile_north_1_east_1': [],
            'tile_north_1_west_1': [],
            'tile_south_1_east_1': [],
            'tile_south_1_west_1': [],
            'tile_north_2': [],
            'tile_north_2_east_1': [],
            'tile_north_2_west_1': [],
            'tile_north_2_east_2': [],
            'tile_north_2_west_2': [],
            'tile_south_2': [],
            'tile_south_2_east_1': [],
            'tile_south_2_west_1': [],
            'tile_south_2_east_2': [],
            'tile_south_2_west_2': [],
            'tile_east_2': [],
            'tile_north_1_east_2': [],
            'tile_south_1_east_2': [],
            'tile_west_2': [],
            'tile_north_1_west_2': [],
            'tile_south_1_west_2': []
            }

DIR = [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1),
       (0, 2), (1, 2), (-1, 2), (2, 2), (-2, 2), (0, -2), (1, -2), (-1, -2), (2, -2),
       (-2, -2), (2, 0), (2, 1), (2, -1), (-2, 0), (-2, 1), (-2, -1)]


class LanguageAgent(ControllerAgent):
    def __init__(self):
        super().__init__()
        if "debug.agentseed" in fc_args:
            self.set_agent_seed(fc_args["debug.agentseed"])

    def act(self, observations, info):
        available_actions = info['available_actions']
        for ctrl_type in available_actions.keys():
            if ctrl_type == 'unit':

                unit_dict = self.get_units_info(observations[ctrl_type], ctrl_type, info)
                # print('unit dict is:', unit_dict)

                valid_actor_id, valid_action_dict = self.get_next_valid_actor(observations, info, ctrl_type)
                if not valid_actor_id:
                    continue

                tile_info = self.get_tile_info(observations[ctrl_type][valid_actor_id])
                # print('tile info is:', tile_info)

                calculate_func = getattr(self, f'calculate_{ctrl_type}_actions')
                action_name = calculate_func(valid_action_dict)
                if action_name:
                    return valid_action_dict[action_name]

            else:
                continue
        return None

    def get_units_info(self, observations, ctrl_type, info):
        unit_dict = {}
        units = list(info['available_actions'][ctrl_type].get_actors())
        for punit in units:
            unit_name = UNIT_TYPES[observations[punit]['utype']]
            unit_dict[unit_name] = {}
            unit_dict[unit_name]['max_move'] = observations[punit]['moves']

            valid_action_dict = self.get_valid_actions(info, ctrl_type, punit)
            unit_dict[unit_name]['avail_actions'] = list(valid_action_dict.keys())
        return unit_dict

    def get_tile_info(self, observation_num):
        tile_info = {}
        tile_id = 0
        for ptile in TILE_INFO_TEMPLATE:
            tile_info[ptile] = []
            pdir = DIR[tile_id]

            terrain = self.terrain_index_to_str(observation_num, pdir)
            if terrain is not None:
                tile_info[ptile].append(terrain)

            extra = self.extra_index_to_str(observation_num, pdir)
            if extra is not None:
                tile_info[ptile].append(extra)

            units = self.unit_index_to_str(observation_num, pdir)
            if len(units) > 0:
                tile_info[ptile].extend(units)

            tile_id += 1
        return tile_info

    def terrain_index_to_str(self, observation_num, pdir):
        terrain_str = None
        dx = RADIUS + pdir[0]
        dy = RADIUS + pdir[1]

        terrain = int(observation_num['terrain'][dx, dy])
        if terrain < len(TERRAIN_NAMES):
            terrain_str = TERRAIN_NAMES[terrain]
        return terrain_str

    def extra_index_to_str(self, observation_num, pdir):
        extra_str = None
        dx = RADIUS + pdir[0]
        dy = RADIUS + pdir[1]

        if observation_num['extras'][dx, dy] == -1:
            return extra_str

        extra = int(observation_num['extras'][dx, dy])
        if extra < len(EXTRA_NAMES):
            extra_str = EXTRA_NAMES[extra]
        return extra_str

    def unit_index_to_str(self, observation_num, pdir):
        unit_str = []
        dx = RADIUS + pdir[0]
        dy = RADIUS + pdir[1]

        units = observation_num['units'][dx, dy, :]
        unit_index = list(np.where(units > 0)[0])
        if len(unit_index) > 0:
            for punit in unit_index:
                punit_number = observation_num['units'][dx, dy, punit]
                punit_name = UNIT_TYPES[punit]
                unit_str.append(str(int(punit_number)) + ' ' + punit_name)
        return unit_str
