# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import random

from gym_freeciv_web.agents.base_agent import BaseAgent
from freecivbot.utils.freeciv_logging import logger


class ControllerAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    def act(self, observations, info):
        for ctrl_type in self.get_ctrl_types(observations):
            valid_actor_id, valid_action_dict = self.get_next_valid_actor(observations, info, ctrl_type)
            if not valid_actor_id:
                continue

            calculate_func = getattr(self, f'calculate_{ctrl_type}_actions')
            action_name = calculate_func(valid_action_dict)
            if action_name:
                return valid_action_dict[action_name]
        return None

    def sample_action_by_prob(self, action_probabilities):
        action_list = list(action_probabilities.keys())
        action_probabilities = list(action_probabilities.values())
        try:
            action_name = random.choices(action_list, weights=action_probabilities, k=1)[0]
            logger.info(f'Action sampled: {action_name}')
            return action_name
        except ValueError:
            # This happens when all action_probabilities are 0.0.
            return None

    def sample_desired_actions(self, action_dict, desired_actions):
        # Use desired_actions = {'': 0.0} for random sample
        action_probabilities = {}
        for action_key in action_dict:
            action_probabilities[action_key] = 0.0
            for desired_action_key in desired_actions:
                if desired_action_key in action_key:
                    action_probabilities[action_key] = desired_actions[desired_action_key]
                    break
        return self.sample_action_by_prob(action_probabilities)

    def calculate_unit_actions(self, action_dict):
        desired_actions = {'explore': 1.0,
                           'goto': random.random()*0.1,
                           # 'autosettlers': 1.0,
                           'build': 1.0}
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_city_actions(self, action_dict):
        desired_actions = {'change_unit_prod_Settlers': 1.0,
                           # 'city_work': random.random()*0.2,
                           'change_improve_prod': random.random()*0.2,
                           'change_unit_prod': random.random()*0.2, }
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_player_actions(self, action_dict):
        desired_actions = {}
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_dipl_actions(self, action_dict):
        desired_actions = {}
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_tech_actions(self, action_dict):
        desired_actions = {'set_tech_goal_Rocketry': 1.0}
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_gov_actions(self, action_dict):
        desired_actions = {}
        return self.sample_desired_actions(action_dict, desired_actions)
