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


from freeciv_gym.envs.freeciv_base_env import FreecivBaseEnv
from freeciv_gym.freeciv.utils.unit_improvement_const import UNIT_TYPES
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.map.map_const import EXTRA_NAMES
from freeciv_gym.freeciv.utils.language_agent_utility import TILE_INFO_TEMPLATE, DIR, get_valid_actions
from freeciv_gym.freeciv.utils.language_agent_utility import get_tile_terrain, get_units_on_tile, action_mask
from freeciv_gym.freeciv.players.player_const import DS_TXT

from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger


class FreecivCodeEnv(FreecivBaseEnv):
    """ Freeciv gym environment with code actions """

    def __init__(self, client_port: int = fc_args['client_port']):
        super().__init__(client_port)

    def get_actor_info(self, info, ctrl_type, actor_id, moves=0, utype=None):
        actor_info = dict()

        actor_name = None
        if ctrl_type == 'unit':
            actor_name = UNIT_TYPES[utype] + ' ' + str(actor_id)
        elif ctrl_type == 'city':
            actor_name = 'City' + ' ' + str(actor_id)
        actor_info[actor_name] = dict()
        actor_info[actor_name]['max_moves'] = moves

        avail_action_set = get_valid_actions(info, ctrl_type, actor_id)

        if not avail_action_set:
            return dict()
        else:
            if ctrl_type == 'unit':
                actor_info[actor_name]['avail_actions'] = avail_action_set
            elif ctrl_type == 'city':
                actor_info[actor_name]['avail_actions'] = action_mask(avail_action_set)

        return actor_info

    def get_mini_map_info(self, ctrl_type, ptile):
        x = ptile['x']
        y = ptile['y']
        mini_map_info = dict()
        info_keys = ['terrain', 'extras', 'units', 'cities']

        tile_id = 0
        for ptile in TILE_INFO_TEMPLATE:
            mini_map_info[ptile] = []
            pdir = DIR[tile_id]
            dx = pdir[0]
            dy = pdir[1]

            if not self.civ_controller.map_ctrl.if_out_mapsize(x + dx, y + dy):
                ntile = self.civ_controller.map_ctrl.map_pos_to_tile(x + dx, y + dy)

                terrain_id = ntile['terrain']
                terrain_str = get_tile_terrain(terrain_id)
                if terrain_str is not None:
                    mini_map_info[ptile].append(terrain_str)

                for extra_id, extra_name in enumerate(EXTRA_NAMES):
                    if ntile['extras'][extra_id] == 1:
                        mini_map_info[ptile].append(extra_name)

                units = ntile['units']
                units_on_tile = get_units_on_tile(units)
                if len(units_on_tile) > 0:
                    mini_map_info[ptile].extend(units_on_tile)

                    units_owner = units[0]['owner']
                    if units_owner == self.civ_controller.player_ctrl.my_player_id:
                        units_dsp = 'Units belong to myself player_' + str(int(units_owner))
                    else:
                        ds_of_units = self.civ_controller.dipl_ctrl.diplstates[units_owner]
                        units_dsp = ('Units belong to a ' + DS_TXT[ds_of_units] + ' player_' + str(int(units_owner)))
                    mini_map_info[ptile].append(units_dsp)

                if ctrl_type == 'unit':
                    pcity = self.civ_controller.city_ctrl.tile_city(ntile)
                    if pcity is not None:
                        city_owner = pcity['owner']
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
        if info['available_actions'] is not None:

            for ctrl_type in info['available_actions']:
                llm_info[ctrl_type] = dict()

                actors_can_act = None
                if ctrl_type in info['available_actions']:
                    actors_can_act = info['available_actions'][ctrl_type]

                if actors_can_act is None:
                    continue

                if ctrl_type == 'unit':
                    units = self.civ_controller.unit_ctrl.units

                    unit_dict = dict()
                    for punit in actors_can_act:
                        if units[punit]['activity'] != 0:
                            continue
                        ptile = self.civ_controller.map_ctrl.index_to_tile(units[punit]['tile'])

                        utype = units[punit]['type']
                        moves = units[punit]['movesleft']
                        actor_info = self.get_actor_info(info, ctrl_type, punit, moves, utype)
                        unit_dict.update(actor_info)
                        llm_info[ctrl_type][punit] = self.get_mini_map_info(ctrl_type, ptile)

                    llm_info[ctrl_type]['unit_dict'] = unit_dict

                elif ctrl_type == 'city':
                    cities = self.civ_controller.city_ctrl.cities

                    city_dict = dict()
                    for pcity in actors_can_act:
                        ptile = self.civ_controller.map_ctrl.index_to_tile(cities[pcity]['tile'])

                        if (self.civ_controller.turn_manager.turn == 1 or
                                self.civ_controller.turn_manager.turn == cities[pcity]['turn_last_built'] + 1):
                            actor_info = self.get_actor_info(info, ctrl_type, pcity, 1)
                        else:
                            actor_info = dict()
                        city_dict.update(actor_info)
                        llm_info[ctrl_type][pcity] = self.get_mini_map_info(ctrl_type, ptile)

                    llm_info[ctrl_type]['city_dict'] = city_dict

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
            assert (False)

        return observation, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        self.civ_controller.init_network()
        info, observation = self._get_info_and_observation()

        llm_info = self.get_llm_info(info)
        info['llm_info'] = llm_info

        return observation, info



