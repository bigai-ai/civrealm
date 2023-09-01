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
import os
from freeciv_gym.agents.base_agent import BaseAgent
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.freeciv.utils.language_agent_utility import MOVE_NAMES, INVERSE_MOVE_NAMES
from freeciv_gym.configs import fc_args

cwd = os.getcwd()


class RuleAgent(BaseAgent):
    def __init__(self, LLM_model='gpt-3.5-turbo', load_dialogue=False):
        super().__init__()
        if fc_args["debug.random_seed"]:
            agentseed = os.getpid()
            self.set_agent_seed(agentseed)
        else:
            if "debug.agentseed" in fc_args:
                self.set_agent_seed(fc_args["debug.agentseed"])

    def act(self, observation, info):
        available_actions = info['available_actions']
        for ctrl_type in available_actions.keys():

            if ctrl_type == 'unit':
                unit_dict = observation[ctrl_type]['unit_dict']
                fc_logger.debug(f'unit_dict: {unit_dict}')
                valid_actor_id, valid_actor_name, valid_action_list = self.get_valid_actor_actions(unit_dict, info, ctrl_type)

                if not valid_actor_id:
                    continue

                current_obs = observation[ctrl_type][valid_actor_id]
                fc_logger.debug(f'current obs: {current_obs}')
                action_name = random.choice(valid_action_list)

                fc_logger.debug(f'unit action: {action_name}')
                return (ctrl_type, valid_actor_id, action_name)

            elif ctrl_type == 'city':
                city_dict = observation[ctrl_type]['city_dict']
                fc_logger.debug(f'city_dict: {city_dict}')
                valid_city_id, valid_city_name, valid_action_list = self.get_valid_actor_actions(city_dict, info, ctrl_type)

                if not valid_city_id:
                    continue

                current_obs = observation[ctrl_type][valid_city_id]
                fc_logger.debug(f'current obs: {current_obs}')
                action_name = random.choice(valid_action_list)

                fc_logger.debug(f'city action: {action_name}')
                return (ctrl_type, valid_city_id, action_name)

            else:
                continue

        return None

    def get_valid_actor_actions(self, actor_dict, info, ctrl_type):
        if info['turn'] != self.turn:
            self.planned_actor_ids = []
            self.turn = info['turn']

        for actor in actor_dict:
            actor_name = actor.split(' ')[0]
            actor_id = int(actor.split(' ')[1])

            if actor_id in self.planned_actor_ids:
                continue

            avail_actions = []
            for action_name in actor_dict[actor]['avail_actions']:
                if info['available_actions'][ctrl_type][actor_id][action_name]:
                    avail_actions.append(action_name)

            self.planned_actor_ids.append(actor_id)
            return actor_id, actor_name, avail_actions

        return None, None, None



