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

    def get_mini_map_info(self, ctrl_type, ptile, moves=0, utype=None):
        mini_map_info = dict()
        info_keys = ['utype', 'moves', 'terrain', 'extras', 'units', 'cities']
        terrain_info, extra_info = self.get_meta_info_of_mini_map(ptile)

        for ptype in info_keys:
            if ctrl_type == 'unit' and ptype == 'utype':
                mini_map_info[ptype] = utype
            elif ptype == 'moves':
                mini_map_info[ptype] = moves
            elif ptype == 'terrain':
                mini_map_info[ptype] = terrain_info
            elif ptype == 'extras':
                mini_map_info[ptype] = extra_info
            elif ptype == 'units':
                mini_map_info[ptype], units_owner, ds_of_units = self.get_units_on_mini_map(ptile)
                mini_map_info['units_owner'] = units_owner
                mini_map_info['ds_of_units'] = ds_of_units
            elif ctrl_type == 'unit' and ptype == 'cities':
                mini_map_info[ptype], ds_of_cites = self.get_cities_on_mini_map(ptile)
                mini_map_info['ds_of_cities'] = ds_of_cites

        return mini_map_info

    def get_meta_info_of_mini_map(self, ptile):
        x = ptile['x']
        y = ptile['y']
        terrain_info = -np.ones((MAP_SIZE, MAP_SIZE))
        extra_info = -np.ones((MAP_SIZE, MAP_SIZE, len(EXTRA_NAMES)))

        for dx in range(-RADIUS, RADIUS+1):
            for dy in range(-RADIUS, RADIUS+1):

                if not self.civ_controller.map_ctrl.if_out_mapsize(x + dx, y + dy):
                    ntile = self.civ_controller.map_ctrl.map_pos_to_tile(x + dx, y + dy)
                    terrain_info[RADIUS + dx, RADIUS + dy] = ntile['terrain']

                    for extra_id, extra_name in enumerate(EXTRA_NAMES):
                        if ntile['extras'][extra_id] == 1:
                            extra_info[RADIUS + dx, RADIUS + dy, extra_id] = 1

        return terrain_info, extra_info

    def get_units_on_mini_map(self, ptile):
        x = ptile['x']
        y = ptile['y']
        units_on_mini_map = np.zeros((MAP_SIZE, MAP_SIZE, len(UNIT_TYPES)))
        units_owner = -np.ones((MAP_SIZE, MAP_SIZE))
        ds_of_units = -np.ones((MAP_SIZE, MAP_SIZE))

        for dx in range(-RADIUS, RADIUS+1):
            for dy in range(-RADIUS, RADIUS+1):

                if not self.civ_controller.map_ctrl.if_out_mapsize(x + dx, y + dy):
                    ntile = self.civ_controller.map_ctrl.map_pos_to_tile(x + dx, y + dy)

                    units_on_ntile = ntile['units']
                    if len(units_on_ntile) == 0:
                        continue

                    # TODO: check if units on the same tile belong to the same owner
                    owner_id = units_on_ntile[0]['owner']
                    units_owner[RADIUS + dx, RADIUS + dy] = owner_id
                    if owner_id != self.civ_controller.player_ctrl.my_player_id:
                        dipl_state = self.civ_controller.dipl_ctrl.diplstates[owner_id]
                        ds_of_units[RADIUS + dx, RADIUS + dy] = dipl_state

                    for punit in units_on_ntile:
                        punit_type = punit['type']
                        units_on_mini_map[RADIUS + dx, RADIUS + dy, punit_type] += 1

        return units_on_mini_map, units_owner, ds_of_units

    def get_cities_on_mini_map(self, ptile):
        x = ptile['x']
        y = ptile['y']
        cities_on_mini_map = -np.ones((MAP_SIZE, MAP_SIZE))
        ds_of_cities = -np.ones((MAP_SIZE, MAP_SIZE))

        for dx in range(-RADIUS, RADIUS+1):
            for dy in range(-RADIUS, RADIUS+1):

                if not self.civ_controller.map_ctrl.if_out_mapsize(x + dx, y + dy):
                    ntile = self.civ_controller.map_ctrl.map_pos_to_tile(x + dx, y + dy)
                    pcity = self.civ_controller.city_ctrl.tile_city(ntile)
                    if pcity is not None:

                        owner_id = pcity['owner']
                        cities_on_mini_map[RADIUS + dx, RADIUS + dy] = owner_id

                        if owner_id != self.civ_controller.player_ctrl.my_player_id:
                            dipl_state = self.civ_controller.dipl_ctrl.diplstates[owner_id]
                            ds_of_cities[RADIUS + dx, RADIUS + dy] = dipl_state

        return cities_on_mini_map, ds_of_cities

    def _get_observation(self):
        base_observations = self.civ_controller.get_observation()

        observations = dict()
        if base_observations is None:
            observations = None
        else:
            for ctrl_type in base_observations:
                if ctrl_type == 'unit':
                    observations[ctrl_type] = dict()
                    units = self.civ_controller.unit_ctrl.units
                    for punit in units:
                        if units[punit]['owner'] != self.civ_controller.player_ctrl.my_player_id:
                            continue

                        ptile = self.civ_controller.map_ctrl.index_to_tile(units[punit]['tile'])
                        unit_mini_map_info = self.get_mini_map_info(ctrl_type, ptile,
                                                                    units[punit]['movesleft'], units[punit]['type'])
                        observations[ctrl_type][punit] = unit_mini_map_info

                elif ctrl_type == 'city':
                    observations[ctrl_type] = dict()
                    cities = self.civ_controller.city_ctrl.cities
                    for pcity in cities:
                        if cities[pcity]['owner'] != self.civ_controller.player_ctrl.my_player_id:
                            continue

                        ptile = self.civ_controller.map_ctrl.index_to_tile(cities[pcity]['tile'])
                        if self.civ_controller.turn_manager.turn == cities[pcity]['turn_last_built'] + 1:
                            city_mini_map_info = self.get_mini_map_info(ctrl_type, ptile, 1)
                        else:
                            city_mini_map_info = self.get_mini_map_info(ctrl_type, ptile)
                        observations[ctrl_type][pcity] = city_mini_map_info

                else:
                    observations[ctrl_type] = base_observations[ctrl_type]

        return observations

