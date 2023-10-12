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
import os
from freeciv_gym.agents.base_agent import BaseAgent
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.freeciv.utils.language_agent_utility import MOVE_NAMES, INVERSE_MOVE_NAMES
from freeciv_gym.configs import fc_args


class RandomLLMAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        if fc_args["debug.randomly_generate_seeds"]:
            agentseed = os.getpid()
            self.set_agent_seed(agentseed)
        else:
            if "debug.agentseed" in fc_args:
                self.set_agent_seed(fc_args["debug.agentseed"])
    
    def act(self, observation, info):
        if info['turn'] != self.turn:
            self.planned_actor_ids = []
            self.turn = info['turn']

        """
        for ctrl_type, actors_dict in info['llm_info'].items():
            for actor_id in actors_dict.keys():
                if actor_id in self.planned_actor_ids:
                    continue
                available_actions = actors_dict[actor_id]['available_actions']
                if available_actions:
                    action_name = random.choice(available_actions)
                    self.planned_actor_ids.append(actor_id)
                    return (ctrl_type, actor_id, action_name)
        """

        for ctrl_type in info['available_actions']:

            """
            if ctrl_type in ['city', 'unit']:
                continue
            """

            for actor_id, action_dict in info['available_actions'][ctrl_type].items():
                if actor_id in self.planned_actor_ids:
                    continue

                for action in list(action_dict.keys()):
                    if not action_dict[action]:
                        del action_dict[action]

                if not action_dict:
                    continue

                action_name = random.choice(list(action_dict.keys()))
                self.planned_actor_ids.append(actor_id)
                return (ctrl_type, actor_id, action_name)

