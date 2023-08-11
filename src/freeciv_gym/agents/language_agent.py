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
from freeciv_gym.freeciv.map.map_const import TERRAIN_NAMES, EXTRA_NAMES, DIR8_NAMES
from freeciv_gym.freeciv.utils.type_const import UNIT_TYPES

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

MOVE_NAMES = {'goto_0': 'move NorthWest', 'goto_1': 'move North', 'goto_2': 'move NorthEast',
              'goto_3': 'move West', 'goto_4': 'move East', 'goto_5': 'move SouthWest',
              'goto_6': 'move South', 'goto_7': 'move SouthEast'}
INVERSE_MOVE_NAMES = {val: key for key, val in MOVE_NAMES.items()}


class LanguageAgent(ControllerAgent):
    def __init__(self):
        super().__init__()
        if "debug.agentseed" in fc_args:
            self.set_agent_seed(fc_args["debug.agentseed"])

    def act(self, observations, info):
        available_actions = info['available_actions']
        for ctrl_type in available_actions.keys():
            if ctrl_type == 'unit':

                unit_dict = self.get_actors_info(observations[ctrl_type], ctrl_type, info)

                valid_actor_id, valid_action_dict = self.get_next_valid_actor(observations, info, ctrl_type)
                if not valid_actor_id:
                    continue

                tile_info = self.get_tiles_info(observations[ctrl_type], valid_actor_id)

                calculate_func = getattr(self, f'calculate_{ctrl_type}_actions')
                action_name = calculate_func(valid_action_dict)
                if action_name:
                    return valid_action_dict[action_name]

            else:
                continue
        return None

    def get_actors_info(self, observations, ctrl_type, info):
        unit_dict = {}
        units = list(info['available_actions'][ctrl_type].get_actors())
        for punit in units:
            unit_name = UNIT_TYPES[observations[punit]['utype']] + ' ' + str(punit)
            unit_dict[unit_name] = {}
            unit_dict[unit_name]['max_move'] = observations[punit]['moves']

            valid_action_dict = self.get_valid_actions(info, ctrl_type, punit)
            avail_actions = list(valid_action_dict.keys())

            for action_id, action_name in enumerate(avail_actions):
                if action_name in MOVE_NAMES:
                    avail_actions[action_id] = MOVE_NAMES[action_name]

            unit_dict[unit_name]['avail_actions'] = avail_actions
        return unit_dict

    def get_tiles_info(self, observations, actor_id):
        observation_num = observations[actor_id]
        tile_info = {}
        tile_id = 0

        for ptile in TILE_INFO_TEMPLATE:
            tile_info[ptile] = []
            pdir = DIR[tile_id]

            terrain = self.get_tile_terrain(observation_num, pdir)
            if terrain is not None:
                tile_info[ptile].append(terrain)

            extra = self.get_tile_extra(observation_num, pdir)
            if extra is not None:
                tile_info[ptile].append(extra)

            units = self.get_units_on_tile(observation_num, pdir)
            if len(units) > 0:
                tile_info[ptile].extend(units)

            tile_id += 1
        return tile_info

    def get_tile_terrain(self, observation_num, pdir):
        terrain_str = None
        dx = RADIUS + pdir[0]
        dy = RADIUS + pdir[1]

        terrain = int(observation_num['terrain'][dx, dy])
        if 0 <= terrain < len(TERRAIN_NAMES):
            terrain_str = TERRAIN_NAMES[terrain]
        return terrain_str

    def get_tile_extra(self, observation_num, pdir):
        extra_str = None
        dx = RADIUS + pdir[0]
        dy = RADIUS + pdir[1]

        extra = int(observation_num['extras'][dx, dy])
        if 0 <= extra < len(EXTRA_NAMES):
            extra_str = EXTRA_NAMES[extra]
        return extra_str

    def get_units_on_tile(self, observation_num, pdir):
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

    def get_actor_action(self, info, ctrl_type, actor_id, action_name):
        valid_action_dict = self.get_valid_actions(info, ctrl_type, actor_id)
        if action_name in INVERSE_MOVE_NAMES:
            action_name = INVERSE_MOVE_NAMES[action_name]

        if action_name in valid_action_dict:
            return valid_action_dict[action_name]
        else:
            raise Exception("Invalid Action !")


'''
tile_info = {'current_tile': ['Forest', '1 Explorer'],
             'tile_north_1': ['Tundra', 'Road', '1 Warriors'],
             'tile_south_1': ['Plains', 'Buffalo'],
             'tile_east_1': ['Mountains'],
             'tile_west_1': ['Hills'],
             'tile_north_1_east_1': ['Swamp', '1 Warriors'],
             'tile_north_1_west_1': ['Forest'],
             'tile_south_1_east_1': ['Forest', '1 Workers'],
             'tile_south_1_west_1': ['Plains'],
             'tile_north_2': ['Mountains', '1 Workers'],
             'tile_north_2_east_1': ['Swamp'],
             'tile_north_2_west_1': ['Swamp'],
             'tile_north_2_east_2': ['Hills'],
             'tile_north_2_west_2': ['Plains'],
             'tile_south_2': ['Mountains'],
             'tile_south_2_east_1': ['Grassland'],
             'tile_south_2_west_1': ['Hills'],
             'tile_south_2_east_2': ['Forest'],
             'tile_south_2_west_2': ['Grassland'],
             'tile_east_2': ['Grassland'],
             'tile_north_1_east_2': ['Hills'],
             'tile_south_1_east_2': ['Forest', 'Pheasant'],
             'tile_west_2': ['Forest'],
             'tile_north_1_west_2': ['Desert'],
             'tile_south_1_west_2': ['Plains']
             }

unit_dict = {'Settlers 101': {'max_move': 0, 'avail_actions': []}, 
             'Workers 103': {'max_move': 3, 'avail_actions': ['disband', 'keep_activity', 'move NorthWest', 
                                                              'move North', 'move NorthEast', 'move West', 
                                                              'move East', 'move SouthWest', 'move South', 
                                                              'move SouthEast']}, 
             'Workers 104': {'max_move': 3, 'avail_actions': ['disband', 'keep_activity', 'move NorthWest', 
                                                              'move North', 'move NorthEast', 'move West', 
                                                              'move East', 'move SouthWest', 'move South', 
                                                              'move SouthEast']}, 
             'Explorer 105': {'max_move': 3, 'avail_actions': ['disband', 'keep_activity', 'explore', 'fortify', 
                                                               'move NorthWest', 'move North', 'move NorthEast', 
                                                               'move West', 'move East', 'move SouthWest', 
                                                               'move South', 'move SouthEast']}
             }
'''


