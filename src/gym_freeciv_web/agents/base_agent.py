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

import time
from freecivbot.civ_controller import CivController
from freecivbot.utils.freeciv_logging import logger

ACTION_UNWANTED = 0
ACTION_WANTED = 1


class BaseAgent(object):
    def __init__(self):
        self.turn_history = []

        self.cur_state = {}
        self.action_options = {}
        self.action_wants = None

    def _calculate_want_of_move(self):
        logger.info("Bot calculates want for controller moves")
        self.action_wants = {}

        for ctrl_type in self.turn_manager.turn_ctrls.keys():
            try:
                calculate_func = getattr(self, f'calculate_{ctrl_type}_actions')
                return calculate_func()
            except AttributeError:
                logger.error(f'Controller type {ctrl_type} is not supported')
                self.action_wants[ctrl_type] = self.calculate_func(ctrl_type)
        return self.action_wants

    def calculate_non_supported_actions(self, ctrl_type):
        """Ensures that non supported actions are "UNWANTED", i.e., will not be triggered"""

        logger.warning('Unsupported actions are set to "UNWANTED"')
        a_options = self._turn_opts[ctrl_type]
        action_wants = {}
        if a_options != None:
            for a_actor in a_options.get_actors():
                action_wants[a_actor] = {}
                for a_action in a_options.get_actions(a_actor):
                    action_wants[a_actor][a_action] = ACTION_UNWANTED
        return action_wants

    def calculate_city_actions(self):
        return self.calculate_non_supported_actions(self._turn_opts["city"])

    def calculate_unit_actions(self):
        return self.calculate_non_supported_actions(self._turn_opts["unit"])

    def calculate_player_actions(self):
        return self.calculate_non_supported_actions(self._turn_opts["player"])

    def calculate_dipl_actions(self):
        return self.calculate_non_supported_actions(self._turn_opts["dipl"])

    def calculate_tech_actions(self):
        return self.calculate_non_supported_actions(self._turn_opts["tech"])

    def calculate_gov_actions(self):
        return self.calculate_non_supported_actions(self._turn_opts["gov"])
