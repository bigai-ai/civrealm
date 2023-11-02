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
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args


class ControllerAgent(BaseAgent):
    def __init__(self, batch_size=1):
        super().__init__(batch_size)
        if fc_args["debug.randomly_generate_seeds"]:
            agentseed = random.randint(0, 999999)
            self.set_agent_seed(agentseed)
        else:
            if "debug.agentseed" in fc_args:
                self.set_agent_seed(fc_args["debug.agentseed"])

    # Each act() lets one actor perform an action.
    def act(self, observations, info):
        if isinstance(observations, tuple) or isinstance(observations, list):
            actions = [None] * len(observations)
            for i in range(len(observations)):
                available_actions = info[i]['available_actions']
                for ctrl_type in available_actions.keys():
                    valid_actor_id, valid_action_dict = self.get_next_valid_actor(observations[i], info[i], ctrl_type, env_id=i)
                    if valid_actor_id is None:
                        continue

                    calculate_func = getattr(self, f'calculate_{ctrl_type}_actions')
                    action_name = calculate_func(valid_action_dict)
                    if action_name is not None:
                        actions[i] = (ctrl_type, valid_actor_id, action_name)
            return actions
        else:
            available_actions = info['available_actions']
            for ctrl_type in available_actions.keys():
                valid_actor_id, valid_action_dict = self.get_next_valid_actor(observations, info, ctrl_type)
                if valid_actor_id is None:
                    continue

                calculate_func = getattr(self, f'calculate_{ctrl_type}_actions')
                action_name = calculate_func(valid_action_dict)
                if action_name is not None:
                    return (ctrl_type, valid_actor_id, action_name)
            return None

    def sample_action_by_prob(self, action_probabilities):
        action_list = list(action_probabilities.keys())
        action_probabilities = list(action_probabilities.values())

        if len(action_probabilities) == 0 or sum(action_probabilities) == 0.0:
            return None

        action_name = random.choices(action_list, weights=action_probabilities, k=1)[0]
        fc_logger.debug(f'Action sampled: {action_name}')
        return action_name

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
        desired_actions = {  # 'explore': 1.0,
            'goto': random.random()*0.2,
            # 'autosettlers': 1.0,
            'road': random.random()*0.2,
            'irrigation': random.random()*0.2,
            'mine': random.random()*0.2,
            'cultivate': random.random()*0.2,
            'plant': random.random()*0.2,
            'pillage': random.random()*0.2,
            'fortress': random.random()*0.2,
            'railroad': random.random()*0.2,
            'airbase': random.random()*0.2,
            'build': 1.0,
            'keep_activity': 1.0}
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_city_actions(self, action_dict):
        desired_actions = {'city_work': random.random() * 0.2,
                           'city_unwork': random.random() * 0.2,
                           'change_improve_prod': random.random() * 0.2,
                           'change_unit_prod': random.random() * 0.2,
                           'city_buy_production': random.random() * 0.2,
                           'city_sell_improvement': random.random() * 0.2,
                           'city_change_specialist': random.random() * 0.2, }
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_player_actions(self, action_dict):
        desired_actions = {}
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_dipl_actions(self, action_dict):
        desired_actions = {'start_negotiation': random.random(),
                           'accept_treaty': random.random(),
                           'cancel_treaty': random.random(),
                           'cancel_vision': random.random(),
                           'stop_negotiation': random.random(),
                           'remove_clause': random.random(),
                           'add_clause': random.random(),
                           'trade_tech_clause': random.random(),
                           'trade_gold_clause': random.random(),
                           'trade_city_clause': random.random(), }
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_tech_actions(self, action_dict):
        desired_actions = {'research_tech': random.random(),
                           'set_tech_goal': random.random(), }
        return self.sample_desired_actions(action_dict, desired_actions)

    def calculate_gov_actions(self, action_dict):
        desired_actions = {'change_gov': random.random(),
                           'increase_sci': random.random(),
                           'decrease_sci': random.random(),
                           'increase_lux': random.random(),
                           'decrease_lux': random.random(),
                           'increase_tax': random.random(),
                           'decrease_tax': random.random(), }
        return self.sample_desired_actions(action_dict, desired_actions)
