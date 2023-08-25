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
import openai
import json
from freeciv_gym.agents.base_agent import BaseAgent
from freeciv_gym.agents.controller_agent import ControllerAgent
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.map.map_const import TERRAIN_NAMES, EXTRA_NAMES, DIR8_NAMES
from freeciv_gym.freeciv.utils.unit_improvement_const import UNIT_TYPES
from freeciv_gym.agents.civ_autogpt.GPTAgent import GPTAgent




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

# Currently not being used.
MOVE_NAMES = {'goto_0': 'move NorthWest', 'goto_1': 'move North', 'goto_2': 'move NorthEast',
              'goto_3': 'move West', 'goto_4': 'move East', 'goto_5': 'move SouthWest',
              'goto_6': 'move South', 'goto_7': 'move SouthEast'}
INVERSE_MOVE_NAMES = {val: key for key, val in MOVE_NAMES.items()}

NUM_TO_DIRECTION_DICT = {'0': 'northwest', '1': 'north', '2': 'northeast', '3': 'west', '4': 'east',
                         '5': 'southwest', '6': 'south', '7': 'southeast'}
DIRECTION_TO_NUM_ACTION_DICT = dict()


class LanguageAgent(ControllerAgent):
    def __init__(self, LLM_model = 'gpt-3.5-turbo'):
        super().__init__()
        if "debug.agentseed" in fc_args:
            self.set_agent_seed(fc_args["debug.agentseed"])
        self.ga = GPTAgent(model = LLM_model)

    def act(self, observations, info):
        available_actions = info['available_actions']
        for ctrl_type in available_actions.keys():
            if ctrl_type == 'unit':

                unit_dict = self.get_actors_info(observations[ctrl_type], ctrl_type, info)

                valid_actor_id, valid_actor_name, valid_action_dict = self.get_next_valid_actor(observations, info, unit_dict, ctrl_type)
                
                if not valid_actor_id:
                    continue
                
                current_unit_name = valid_actor_name
                current_obs = self.get_tiles_info(observations[ctrl_type], valid_actor_id)
                print('current obs:', current_obs)
                current_avail_actions_list = []

                for action_name in valid_action_dict.keys():
                    temp_name = action_name
                    if action_name[-1] in NUM_TO_DIRECTION_DICT.keys():
                        current_avail_actions_list.append(action_name[:-1] + NUM_TO_DIRECTION_DICT[action_name[-1]])
                    else:
                        current_avail_actions_list.append(action_name)
                    DIRECTION_TO_NUM_ACTION_DICT[current_avail_actions_list[-1]] = temp_name

                obs_input_prompt = f"""The unit is {current_unit_name}, observation is {current_obs}. Your available action list is {current_avail_actions_list}. """
                
                print('current unit:', current_unit_name, '; unit id:', valid_actor_id)
                
                exec_action_name = None
                while exec_action_name is None:
                    response = self.ga.communicate(obs_input_prompt, parse_choice_tag = False)
                    self.ga.memory.save_context({'user': obs_input_prompt}, {'assistant': str(response)})
                    if isinstance(response, str):
                        response = json.loads(response)

                    exec_action_name = self.ga.process_command(response['command'], obs_input_prompt, current_unit_name, current_avail_actions_list)

                exec_action_name = DIRECTION_TO_NUM_ACTION_DICT[exec_action_name]
                if exec_action_name:
                    return valid_action_dict[exec_action_name]

            else:
                continue
        return None
    
    def get_next_valid_actor(self, observations, info, unit_dict, desired_ctrl_type=None):
        """
        Return the first actable actor_id and its valid_action_dict that has not been planned in this turn.
        The v1 version does not have a choosing mechanism, so just chooses the first one like former. 
        But we should rewrite it in the next version.
        """
        # TODO: Do we need the turn variable for Agent class?
        if info['turn'] != self.turn:
            self.planned_actor_ids = []
            self.turn = info['turn']

        available_actions = info['available_actions']
        for ctrl_type in available_actions.keys():
            if desired_ctrl_type and desired_ctrl_type != ctrl_type:
                continue

            action_list = available_actions[ctrl_type]
            for actor_id in action_list.get_actors():
                # TODO: We need to write the choosing mechanism in the following version.
                if actor_id in self.planned_actor_ids:
                    # We have planned an action for this actor in this turn.
                    continue_flag = 0
                    for id in unit_dict.keys():
                        if actor_id == int(id.split(' ')[-1]):
                            # For those not explorer, we only let them move once.
                            if id.split(' ')[0] != 'Explorer':
                                continue_flag = 1
                                break
                            if unit_dict[id]['max_move'] <= 0:
                                continue_flag = 1
                                break
                    if continue_flag == 1:
                        continue

                if action_list._can_actor_act(actor_id):
                    fc_logger.debug(f'Trying to operate actor_id {actor_id} by {ctrl_type}_ctrl')
                    valid_action_dict = action_list.get_actions(actor_id, valid_only=True)
                    if not valid_action_dict:
                        continue

                    fc_logger.debug(
                        f'{ctrl_type}_ctrl: Valid actor_id {actor_id} with valid actions found {valid_action_dict}')
                    self.planned_actor_ids.append(actor_id)
                    actor_name = None
                    for id in unit_dict.keys():
                        if actor_id == int(id.split(' ')[-1]):
                            actor_name = id.split(' ')[0]
                            break
                    return actor_id, actor_name, valid_action_dict

        return None, None, None

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

            units, units_owner = self.get_units_on_tile(observation_num, pdir)
            if len(units) > 0:
                tile_info[ptile].extend(units)

            if units_owner is not None:
                tile_info[ptile].append('Units belong to player_' + str(int(units_owner)))

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
        units_str = []
        units_owner = None
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
        return units_str, units_owner

    def get_actor_action(self, info, ctrl_type, actor_id, action_name):
        valid_action_dict = self.get_valid_actions(info, ctrl_type, actor_id)
        if action_name in INVERSE_MOVE_NAMES:
            action_name = INVERSE_MOVE_NAMES[action_name]

        if action_name in valid_action_dict:
            return valid_action_dict[action_name]
        else:
            raise Exception("Invalid Action !")


'''
tile_info = {'current_tile': ['Forest', '1 Explorer', 'Units belong to player_0'],
             'tile_north_1': ['Tundra', 'Road', '1 Warriors', 'Units belong to player_0'],
             'tile_south_1': ['Plains', 'Buffalo'],
             'tile_east_1': ['Mountains'],
             'tile_west_1': ['Hills'],
             'tile_north_1_east_1': ['Swamp', '1 Warriors', 'Units belong to player_0'],
             'tile_north_1_west_1': ['Forest'],
             'tile_south_1_east_1': ['Forest', '1 Workers', 'Units belong to player_0'],
             'tile_south_1_west_1': ['Plains'],
             'tile_north_2': ['Mountains', '1 Workers', 'Units belong to player_0'],
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

