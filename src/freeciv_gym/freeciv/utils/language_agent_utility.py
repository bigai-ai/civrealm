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
from freeciv_gym.freeciv.map.map_const import TERRAIN_NAMES
from freeciv_gym.freeciv.utils.unit_improvement_const import UNIT_TYPES

RADIUS = 2
MAP_SIZE = RADIUS * 2 + 1
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

MOVE_NAMES = {'goto_0': 'move_NorthWest', 'goto_1': 'move_North', 'goto_2': 'move_NorthEast',
              'goto_3': 'move_West', 'goto_4': 'move_East', 'goto_5': 'move_SouthWest',
              'goto_6': 'move_South', 'goto_7': 'move_SouthEast'}
INVERSE_MOVE_NAMES = {val: key for key, val in MOVE_NAMES.items()}

KEYWORDS = ['change_unit_prod', 'change_improve_prod']


def action_mask(avail_action_set):
    action_names = []
    for act in avail_action_set:
        for keyword in KEYWORDS:
            if keyword in act:
                action_names.append(act)
    return action_names


def get_tile_terrain(terrain_id):
    terrain_str = None

    if 0 <= terrain_id < len(TERRAIN_NAMES):
        terrain_str = TERRAIN_NAMES[terrain_id]
    return terrain_str


def get_units_on_tile(units):
    units_on_tile = []
    units_on_tile_count = [0] * len(UNIT_TYPES)
    for punit in units:
        punit_type = punit['type']
        units_on_tile_count[punit_type] += 1

    for unit_id, unit_name in enumerate(UNIT_TYPES):
        units_num = units_on_tile_count[unit_id]
        if units_num > 0:
            units_on_tile.append(str(int(units_num)) + ' ' + unit_name)
    return units_on_tile


def get_valid_actions(info, ctrl_type, actor_id):
    action_dict = info['available_actions'][ctrl_type]
    avail_action_set = []

    for actor_act in action_dict[actor_id]:
        if action_dict[actor_id][actor_act]:
            avail_action_set.append(actor_act)
    return avail_action_set

