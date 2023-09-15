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
import time
import json
from freeciv_gym.agents.base_agent import BaseAgent
from freeciv_gym.agents.controller_agent import ControllerAgent
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.map.map_const import TERRAIN_NAMES, EXTRA_NAMES, DIR8_NAMES
from freeciv_gym.freeciv.utils.unit_improvement_const import UNIT_TYPES
from freeciv_gym.agents.civ_autogpt.GPTAgent import GPTAgent
from freeciv_gym.freeciv.players.player_const import DS_TXT


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

DIR = [(0, 0), (0, -1), (0, 1), (1, 0), (-1, 0), (1, -1), (-1, -1), (1, 1), (-1, 1),
       (0, -2), (1, -2), (-1, -2), (2, -2), (-2, -2), (0, 2), (1, 2), (-1, 2), (2, 2),
       (-2, 2), (2, 0), (2, -1), (2, 1), (-2, 0), (-2, -1), (-2, 1)]

# Currently not being used.
MOVE_NAMES = {'goto_0': 'move NorthWest', 'goto_1': 'move North', 'goto_2': 'move NorthEast',
              'goto_3': 'move West', 'goto_4': 'move East', 'goto_5': 'move SouthWest',
              'goto_6': 'move South', 'goto_7': 'move SouthEast'}
INVERSE_MOVE_NAMES = {val: key for key, val in MOVE_NAMES.items()}

NUM_TO_DIRECTION_DICT = {'0': 'northwest', '1': 'north', '2': 'northeast', '3': 'west', '4': 'east',
                         '5': 'southwest', '6': 'south', '7': 'southeast'}
DIRECTION_TO_NUM_ACTION_DICT = dict()
KEYWORDS = ['change_unit_prod', 'change_improve_prod']

class LanguageAgent(ControllerAgent):
    def __init__(self, LLM_model = 'gpt-3.5-turbo'):
        super().__init__()
        if "debug.agentseed" in fc_args:
            self.set_agent_seed(fc_args["debug.agentseed"])
        self.gpt_agent = GPTAgent(model = LLM_model)

    def act(self, observations, info):
        available_actions = info['available_actions']
        for ctrl_type in available_actions.keys():
            if ctrl_type == 'unit':

                unit_dict = get_actors_info(observations, ctrl_type, info)
                fc_logger.debug(f'unit_dict: {unit_dict}')
                valid_actor_id, valid_actor_name, valid_action_dict = self.get_next_valid_actor(observations, info,
                                                                                                unit_dict, ctrl_type)
                
                if not valid_actor_id:
                    continue
                
                current_unit_name = valid_actor_name
                current_obs = get_tiles_info(observations, ctrl_type, valid_actor_id)
                fc_logger.debug(f'unit current obs: {current_obs}')

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
                start_time = time.time()
                while exec_action_name is None:
                    end_time = time.time()
                    if (end_time - start_time) >= 120:
                        exec_action_name = random.choice(current_avail_actions_list)
                        self.gpt_agent.dialogue.pop(-1)
                        self.gpt_agent.dialogue.pop(-1)
                        print('overtime, randomly choose:', exec_action_name)
                        break
                    response = self.gpt_agent.communicate(obs_input_prompt, parse_choice_tag = False)
                    self.gpt_agent.memory.save_context({'user': obs_input_prompt}, {'assistant': str(response)})
                    exec_action_name = self.gpt_agent.process_command(response, obs_input_prompt, current_unit_name, current_avail_actions_list)

                exec_action_name = DIRECTION_TO_NUM_ACTION_DICT[exec_action_name]
                if exec_action_name:
                    return valid_action_dict[exec_action_name]

            elif ctrl_type == 'city':
                city_dict = get_actors_info(observations, ctrl_type, info)
                fc_logger.debug(f'city_dict: {city_dict}')

                valid_city_id, current_city_name, valid_city_actions_list = self.get_next_valid_actor(observations, info,
                                                                                                city_dict, ctrl_type)
                
                if not valid_city_id:
                    continue

                current_city_obs = get_tiles_info(observations, ctrl_type, valid_city_id)

                current_city_avail_actions_list = [action_name for action_name in valid_city_actions_list.keys()]

                obs_input_prompt = f"""The city is {current_city_name}, observation is {current_city_obs}. Your available action list is {current_city_avail_actions_list}. """
                print('current city:', current_city_name, '; city id:', valid_city_id)

                fc_logger.debug(f'city current obs: {current_city_obs}')

                exec_action_name = None
                start_time = time.time()
                while exec_action_name is None:
                    end_time = time.time()
                    if (end_time - start_time) >= 120:
                        exec_action_name = random.choice(current_city_avail_actions_list)
                        self.gpt_agent.dialogue.pop(-1)
                        self.gpt_agent.dialogue.pop(-1)
                        print('overtime, randomly choose:', exec_action_name)
                        break
                    response = self.gpt_agent.communicate(obs_input_prompt, parse_choice_tag = False)
                    self.gpt_agent.update_key()
                    self.gpt_agent.memory.save_context({'user': obs_input_prompt}, {'assistant': str(response)})
                    exec_action_name = self.gpt_agent.process_command(response, obs_input_prompt, current_city_name, current_city_avail_actions_list)

                if exec_action_name:
                    return valid_city_actions_list[exec_action_name]

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
                    # # We have planned an action for this actor in this turn.
                    # continue_flag = 0
                    # for id in unit_dict.keys():
                    #     if actor_id == int(id.split(' ')[-1]):
                    #         # For those not explorer, we only let them move once.
                    #         if id.split(' ')[0] != 'Explorer':
                    #             continue_flag = 1
                    #             break
                    #         if unit_dict[id]['max_move'] <= 0:
                    #             continue_flag = 1
                    #             break
                    # if continue_flag == 1:
                    #     continue
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


def get_actors_info(observations, ctrl_type, info):
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

        valid_action_dict = action_mask(get_valid_actions(info, ctrl_type, pactor))
        avail_actions = list(valid_action_dict.keys())

        if ctrl_type == 'unit':
            for action_id, action_name in enumerate(avail_actions):
                if action_name in MOVE_NAMES:
                    avail_actions[action_id] = MOVE_NAMES[action_name]

        actor_dict[actor_name]['avail_actions'] = avail_actions
    return actor_dict


def get_valid_actions(info, ctrl_type, actor_id):
    available_actions = info['available_actions']
    action_list = available_actions[ctrl_type]

    valid_action_dict = action_list.get_actions(actor_id, valid_only=True)
    return valid_action_dict


def action_mask(valid_action_dict):
    action_names = dict()
    for act in valid_action_dict:
        for keyword in KEYWORDS:
            if keyword in act:
                action_names[act] = valid_action_dict[act]
    return action_names


def get_tiles_info(observations, ctrl_type, actor_id):
    observation_num = observations[ctrl_type][actor_id]
    tile_info = dict()
    tile_id = 0

    for ptile in TILE_INFO_TEMPLATE:
        tile_info[ptile] = []
        pdir = DIR[tile_id]

        terrain = get_tile_terrain(observation_num, pdir)
        if terrain is not None:
            tile_info[ptile].append(terrain)

        extra = get_tile_extra(observation_num, pdir)
        if len(extra) > 0:
            tile_info[ptile].extend(extra)

        units_str, units_dsp = get_units_on_tile(observation_num, pdir)
        if len(units_str) > 0:
            tile_info[ptile].extend(units_str)
        if units_dsp is not None:
            tile_info[ptile].append(units_dsp)

        if ctrl_type == 'unit':
            player_of_city, city_dsp = get_city_on_tile(observation_num, pdir)
            if city_dsp is not None:
                tile_info[ptile].append(city_dsp)

        tile_id += 1
    return tile_info


def get_tile_terrain(observation_num, pdir):
    terrain_str = None
    dx = RADIUS + pdir[0]
    dy = RADIUS + pdir[1]

    terrain = int(observation_num['terrain'][dx, dy])
    if 0 <= terrain < len(TERRAIN_NAMES):
        terrain_str = TERRAIN_NAMES[terrain]
    return terrain_str


def get_tile_extra(observation_num, pdir):
    extra_str = []
    dx = RADIUS + pdir[0]
    dy = RADIUS + pdir[1]

    for extra_id, extra_name in enumerate(EXTRA_NAMES):
        if observation_num['extras'][dx, dy][extra_id] == 1:
            extra_str.append(extra_name)
    return extra_str


def get_units_on_tile(observation_num, pdir):
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


def get_city_on_tile(observation_num, pdir):
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


"""
tile_info = {'current_tile': ['Forest', '1 Explorer', 'Units belong to myself player_0'],
             'tile_north_1': ['Tundra', 'Road', '1 Warriors', 'Units belong to myself player_0'],
             'tile_south_1': ['Plains', 'Buffalo'],
             'tile_east_1': ['Mountains'],
             'tile_west_1': ['Hills'],
             'tile_north_1_east_1': ['Swamp', '1 Warriors', 'Units belong to myself player_0'],
             'tile_north_1_west_1': ['Forest'],
             'tile_south_1_east_1': ['Forest', '1 Workers', 'Units belong to myself player_0'],
             'tile_south_1_west_1': ['Plains'],
             'tile_north_2': ['Mountains', '1 Workers', 'Units belong to myself player_0', 
                              '1 city belongs to myself player_0'],
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

city_dict: {'city 121': {'max_move': 0, 'avail_actions': ['change_unit_prod_Settlers_0',
                                                          'change_improve_prod_Barracks_3']},
            'city 129': {'max_move': 0, 'avail_actions': ['change_unit_prod_Settlers_0',
                                                          'change_improve_prod_Barracks_3']}
            }

city_tile_info: {'current_tile': ['Plains', 'Road', 'Wheat'],
                 'tile_north_1': ['Forest'], 
                 'tile_south_1': ['Forest'], 
                 'tile_east_1': ['Ocean'],
                 'tile_west_1': ['Grassland'], 
                 'tile_north_1_east_1': ['Forest', 'Minor Tribe Village'],
                 'tile_north_1_west_1': ['Plains'],
                 'tile_south_1_east_1': ['Ocean'],
                 'tile_south_1_west_1': ['Swamp'],
                 'tile_north_2': ['Plains'],
                 'tile_north_2_east_1': ['Ocean'],
                 'tile_north_2_west_1': ['Forest'], 'tile_north_2_east_2': ['Ocean'],
                 'tile_north_2_west_2': ['Swamp'],
                 'tile_south_2': ['Grassland'],
                 'tile_south_2_east_1': ['Ocean', 'Fish'],
                 'tile_south_2_west_1': ['Forest', 'Pheasant'],
                 'tile_south_2_east_2': ['Grassland'],
                 'tile_south_2_west_2': ['Grassland'],
                 'tile_east_2': ['Ocean'],
                 'tile_north_1_east_2': ['Grassland', 'Resources'],
                 'tile_south_1_east_2': ['Ocean'],
                 'tile_west_2': ['Mountains'],
                 'tile_north_1_west_2': ['Mountains'],
                 'tile_south_1_west_2': ['Grassland']
                 }
"""
