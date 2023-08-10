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

from freeciv_gym.agents.base_agent import BaseAgent
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args


class LanguageAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        if "debug.agentseed" in fc_args:
            self.set_agent_seed(fc_args["debug.agentseed"])

    def act(self, observations, info):

        observation_of_mini_map = observations['unit']

        available_actions = info['available_actions']
        for ctrl_type in available_actions.keys():
            if ctrl_type == 'unit':

                # TODO：Language model to choose a unit to act
                valid_actor_id, valid_action_dict = self.get_next_valid_actor(observations, info, ctrl_type)
                if not valid_actor_id:
                    continue

                # TODO: Language model to choose an action for the selected unit
                calculate_func = getattr(self, f'calculate_{ctrl_type}_actions')
                action_name = calculate_func(valid_action_dict)
                if action_name:
                    return valid_action_dict[action_name]
            else:
                continue

        return None

    def sample_action_by_prob(self, action_probabilities):
        action_list = list(action_probabilities.keys())
        action_probabilities = list(action_probabilities.values())
        try:
            action_name = random.choices(action_list, weights=action_probabilities, k=1)[0]
            fc_logger.info(f'Action sampled: {action_name}')
            return action_name
        except ValueError:
            return None

    def sample_desired_actions(self, action_dict, desired_actions):
        action_probabilities = {}
        for action_key in action_dict:
            action_probabilities[action_key] = 0.0
            for desired_action_key in desired_actions:
                if desired_action_key in action_key:
                    action_probabilities[action_key] = desired_actions[desired_action_key]
                    break
        return self.sample_action_by_prob(action_probabilities)

    def calculate_unit_actions(self, action_dict):
        desired_actions = {'goto': random.random() * 0.2,
                           'road': random.random() * 0.2,
                           'irrigation': random.random() * 0.2,
                           'mine': random.random() * 0.2,
                           'cultivate': random.random() * 0.2,
                           'plant': random.random() * 0.2,
                           'pillage': random.random() * 0.2,
                           'fortress': random.random() * 0.2,
                           'railroad': random.random() * 0.2,
                           'airbase': random.random() * 0.2,
                           'build': 1.0}
        return self.sample_desired_actions(action_dict, desired_actions)


