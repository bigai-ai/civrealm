# Copyright (C) 2023  The CivRealm project
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
from civrealm.agents.base_agent import BaseAgent
from civrealm.configs import fc_args


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

        for ctrl_type, actors_dict in info['llm_info'].items():
            for actor_id in actors_dict.keys():
                if actor_id in self.planned_actor_ids:
                    continue
                available_actions = actors_dict[actor_id]['available_actions']
                if available_actions:
                    action_name = random.choice(available_actions)
                    self.planned_actor_ids.append(actor_id)
                    return (ctrl_type, actor_id, action_name)
