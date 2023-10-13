# Copyright (C) 2023  The CivRealm project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR action_optsA PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import random

from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.agents.base_agent import BaseAgent


class RandomAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    def random_action_by_name(self, valid_action_dict, name):
        # Assume input actions are valid, and return a random choice of the actions whose name contains the input name.
        action_choices = [key for key in valid_action_dict.keys() if name in key]
        if action_choices:
            return random.choice(action_choices)
        else:
            return None

    def act(self, observations, info):
        unit_actor, unit_action_dict = self.get_next_valid_actor(observations, info, 'unit')
        fc_logger.info(f'Valid actions: {unit_action_dict}')
        if not unit_actor:
            return None

        # Try to build a city
        build_action = self.random_action_by_name(unit_action_dict, 'build')
        if build_action and random.random() > 0.2:
            return 'unit', unit_actor, build_action

        # Try to move
        return 'unit', unit_actor, self.random_action_by_name(unit_action_dict, 'goto')
