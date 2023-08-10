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

import gymnasium
import numpy as np

from freeciv_gym.envs.freeciv_base_env import FreecivBaseEnv
from freeciv_gym.freeciv.utils.type_const import UNIT_TYPES
RADIUS = 2


class FreecivCodeEnv(FreecivBaseEnv):
    """ Freeciv gym environment with code actions """

    def __init__(self):
        super().__init__()

    def get_mini_map_info(self, ptile):
        x = ptile['x']
        y = ptile['y']
        map_info = self.civ_controller.controller_list['map'].prop_state._state

        mini_map_info = {}
        info_keys = ['status', 'terrain', 'extras', 'units']
        for ptype in info_keys:
            if ptype in ['status', 'terrain']:
                mini_map_info[ptype] = map_info[ptype][x-RADIUS: x+RADIUS+1, y-RADIUS: y+RADIUS+1]
            elif ptype == 'extras':
                mini_map_info[ptype] = map_info[ptype][x-RADIUS: x+RADIUS+1, y-RADIUS: y+RADIUS+1, :]
            else:
                mini_map_info[ptype] = self.get_units_on_mini_map(ptile)
        return mini_map_info

    def get_units_on_mini_map(self, ptile):
        number_of_unit_types = len(UNIT_TYPES)
        units_on_mini_map = np.zeros((2*RADIUS+1, 2*RADIUS+1, number_of_unit_types))

        x = ptile['x']
        y = ptile['y']
        for dx in range(-RADIUS, RADIUS+1):
            for dy in range(RADIUS, RADIUS+1):
                ntile = self.civ_controller.controller_list['map'].map_pos_to_tile(x+dx, y+dy)
                units_on_ntile = ntile['units']
                if len(units_on_ntile) == 0:
                    continue
                for punit in units_on_ntile:
                    punit_type = punit['type']
                    units_on_mini_map[RADIUS+dx, RADIUS+dy, punit_type] += 1
        return units_on_mini_map

    def _get_observation(self):
        self.civ_controller.lock_control()
        self.civ_controller.turn_manager.get_observation()
        turn_manager = self.civ_controller.turn_manager
        pplayer = turn_manager._turn_player

        observations = {}
        for ctrl_type, ctrl in turn_manager._turn_ctrls.items():
            if ctrl_type == 'unit':
                observations[ctrl_type] = {}
                units = self.civ_controller.controller_list['unit'].units
                for punit in units:
                    ptile = self.civ_controller.controller_list['map'].index_to_tile(units[punit]['tile'])
                    mini_map_info = self.get_mini_map_info(ptile)
                    observations[ctrl_type][punit] = mini_map_info
            else:
                observations[ctrl_type] = ctrl.get_current_state(pplayer)

        return observations

