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
from freeciv_gym.freeciv.players.player_const import DS_TXT

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

# Currently not being used.
MOVE_NAMES = {'goto_0': 'move_NorthWest', 'goto_1': 'move_North', 'goto_2': 'move_NorthEast',
              'goto_3': 'move_West', 'goto_4': 'move_East', 'goto_5': 'move_SouthWest',
              'goto_6': 'move_South', 'goto_7': 'move_SouthEast'}
INVERSE_MOVE_NAMES = {val: key for key, val in MOVE_NAMES.items()}

KEYWORDS = ['change_unit_prod', 'change_improve_prod']


class FreecivCodeEnv(FreecivBaseEnv):
    """ Freeciv gym environment with code actions """

    def __init__(self, client_port: int = fc_args['client_port']):
        super().__init__(client_port)
        self.MOVE_NAMES = MOVE_NAMES
        self.INVERSE_MOVE_NAMES = INVERSE_MOVE_NAMES

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

    def get_city_on_tile(self, observation_num, pdir):
        player_of_city = None
        city_dsp = None
        dx = RADIUS + pdir[0]
        dy = RADIUS + pdir[1]

        city_owner = observation_num['cities'][dx, dy]
        ds_of_city = observation_num['ds_of_cities'][dx, dy]
        if city_owner >= 0:
            player_of_city = int(city_owner)

            if ds_of_city >= 0:
                ds_of_city = int(ds_of_city)
                city_dsp = '1 city belongs to a ' + DS_TXT[ds_of_city] + ' player_' + str(player_of_city)
            else:
                city_dsp = '1 city belongs to myself player_' + str(player_of_city)

        return player_of_city, city_dsp
    
    def get_actors_info(self, observations, ctrl_type, info):
        observation_ctrl = observations[ctrl_type]
        actor_dict = dict()
        actors = list(info['available_actions'][ctrl_type].get_actors())
        for pactor in actors:
            actor_name = None
            if ctrl_type == 'unit':
                actor_name = UNIT_TYPES[observation_ctrl[pactor]['utype']] + ' ' + str(pactor)
            elif ctrl_type == 'city':
                actor_name = 'city' + ' ' + str(pactor)

            actor_dict[actor_name] = dict()
            actor_dict[actor_name]['max_move'] = observation_ctrl[pactor]['moves']

            valid_action_dict = self.action_mask(self.get_valid_actions(info, ctrl_type, pactor))
            avail_actions = list(valid_action_dict.keys())

            if ctrl_type == 'unit':
                for action_id, action_name in enumerate(avail_actions):
                    if action_name in MOVE_NAMES:
                        avail_actions[action_id] = MOVE_NAMES[action_name]

            actor_dict[actor_name]['avail_actions'] = avail_actions
        return actor_dict

    def get_valid_actions(self, info, ctrl_type, actor_id):
        available_actions = info['available_actions']
        action_list = available_actions[ctrl_type]

        valid_action_dict = action_list.get_actions(actor_id, valid_only=True)
        return valid_action_dict


    def action_mask(self, valid_action_dict):
        action_names = dict()
        for act in valid_action_dict:
            for keyword in KEYWORDS:
                if keyword in act:
                    action_names[act] = valid_action_dict[act]
        return action_names


    def get_tiles_info(self, observations, ctrl_type, actor_id):
        observation_num = observations[ctrl_type][actor_id]
        tile_info = dict()
        tile_id = 0

        for ptile in TILE_INFO_TEMPLATE:
            tile_info[ptile] = []
            pdir = DIR[tile_id]

            terrain = self.get_tile_terrain(observation_num, pdir)
            if terrain is not None:
                tile_info[ptile].append(terrain)

            extra = self.get_tile_extra(observation_num, pdir)
            if len(extra) > 0:
                tile_info[ptile].extend(extra)

            units_str, units_dsp = self.get_units_on_tile(observation_num, pdir)
            if len(units_str) > 0:
                tile_info[ptile].extend(units_str)
            if units_dsp is not None:
                tile_info[ptile].append(units_dsp)

            if ctrl_type == 'unit':
                player_of_city, city_dsp = self.get_city_on_tile(observation_num, pdir)
                if city_dsp is not None:
                    tile_info[ptile].append(city_dsp)

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
        extra_str = []
        dx = RADIUS + pdir[0]
        dy = RADIUS + pdir[1]

        for extra_id, extra_name in enumerate(EXTRA_NAMES):
            if observation_num['extras'][dx, dy][extra_id] == 1:
                extra_str.append(extra_name)
        return extra_str


    def get_units_on_tile(self, observation_num, pdir):
        units_str = []
        units_dsp = None
        dx = RADIUS + pdir[0]
        dy = RADIUS + pdir[1]

        units = observation_num['units'][dx, dy, :]
        unit_index = list(np.where(units > 0)[0])
        if len(unit_index) > 0:
            for punit in unit_index:
                punit_number = observation_num['units'][dx, dy, punit]
                punit_name = UNIT_TYPES[punit]
                units_str.append(str(int(punit_number)) + ' ' + punit_name)

            units_owner = observation_num['units_owner'][dx, dy]
            ds_of_units = observation_num['ds_of_units'][dx, dy]

            if ds_of_units >= 0:
                ds_of_units = int(ds_of_units)
                units_dsp = 'Units belong to a ' + DS_TXT[ds_of_units] + ' player_' + str(int(units_owner))
            else:
                units_dsp = 'Units belong to myself player_' + str(int(units_owner))

        return units_str, units_dsp
