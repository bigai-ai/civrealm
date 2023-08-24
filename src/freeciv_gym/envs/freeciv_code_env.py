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
RADIUS = 2
MAP_SIZE = RADIUS * 2 + 1


class FreecivCodeEnv(FreecivBaseEnv):
    """ Freeciv gym environment with code actions """

    def __init__(self, client_port: int = fc_args['client_port']):
        super().__init__(client_port)

    def get_mini_map_info(self, utype, moves, ptile):
        mini_map_info = {}
        info_keys = ['utype', 'moves', 'terrain', 'extras', 'units']
        terrain_info, extra_info = self.get_meta_info_of_mini_map(ptile)

        for ptype in info_keys:
            if ptype == 'utype':
                mini_map_info[ptype] = utype
            elif ptype == 'moves':
                mini_map_info[ptype] = moves
            elif ptype == 'terrain':
                mini_map_info[ptype] = terrain_info
            elif ptype == 'extras':
                mini_map_info[ptype] = extra_info
            else:
                mini_map_info[ptype] = self.get_units_on_mini_map(ptile)
        return mini_map_info

    def get_meta_info_of_mini_map(self, ptile):
        x = ptile['x']
        y = ptile['y']
        terrain_info = np.zeros((MAP_SIZE, MAP_SIZE))
        extra_info = np.zeros((MAP_SIZE, MAP_SIZE))

        for dx in range(-RADIUS, RADIUS+1):
            for dy in range(-RADIUS, RADIUS+1):
                terrain = -1
                extra = -1

                if not self.civ_controller.controller_list['map'].if_out_mapsize(x + dx, y + dy):
                    ntile = self.civ_controller.controller_list['map'].map_pos_to_tile(x + dx, y + dy)
                    terrain = ntile['terrain']
                    for extra_id in range(len(EXTRA_NAMES)):
                        if ntile['extras'][extra_id] == 1:
                            extra = extra_id
                            break

                terrain_info[RADIUS+dx, RADIUS+dy] = terrain
                extra_info[RADIUS+dx, RADIUS+dy] = extra
        return terrain_info, extra_info

    def get_units_on_mini_map(self, ptile):
        x = ptile['x']
        y = ptile['y']
        number_of_unit_types = len(UNIT_TYPES)
        units_on_mini_map = np.zeros((MAP_SIZE, MAP_SIZE, number_of_unit_types))

        for dx in range(-RADIUS, RADIUS+1):
            for dy in range(-RADIUS, RADIUS+1):
                if not self.civ_controller.controller_list['map'].if_out_mapsize(x + dx, y + dy):
                    ntile = self.civ_controller.controller_list['map'].map_pos_to_tile(x + dx, y + dy)
                    units_on_ntile = ntile['units']
                    if len(units_on_ntile) == 0:
                        continue
                    for punit in units_on_ntile:
                        punit_type = punit['type']
                        units_on_mini_map[RADIUS + dx, RADIUS + dy, punit_type] += 1

        return units_on_mini_map

    def _get_observation(self):
        self.civ_controller.lock_control()
        self.civ_controller.turn_manager.get_observation()
        turn_manager = self.civ_controller.turn_manager

        observations = {}
        for ctrl_type, ctrl in turn_manager._turn_ctrls.items():
            if ctrl_type == 'unit':
                observations[ctrl_type] = {}
                units = self.civ_controller.controller_list['unit'].units
                for punit in units:
                    if units[punit]['owner'] != self.civ_controller.controller_list['player'].my_player_id:
                        continue

                    ptile = self.civ_controller.controller_list['map'].index_to_tile(units[punit]['tile'])
                    mini_map_info = self.get_mini_map_info(units[punit]['type'], units[punit]['movesleft'], ptile)
                    observations[ctrl_type][punit] = mini_map_info
            else:
                observations[ctrl_type] = turn_manager._turn_state[ctrl_type]

        return observations
