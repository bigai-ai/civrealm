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

from random import random

from freecivbot.bot.base_bot import ACTION_WANTED, ACTION_UNWANTED, BaseBot
from freecivbot.civ_controller import CivController
from freecivbot.connectivity.clinet import CivConnection


class SimpleBot(BaseBot):
    def calculate_unit_actions(self):
        a_options = self._turn_opts["unit"]
        action_wants = {}
        for unit_id in a_options.get_actors():
            action_wants[unit_id] = {}
            actions = a_options.get_actions(unit_id, valid_only=True)
            for action_key in actions:
                if actions[action_key] is None:
                    continue
                if action_key == "explore":
                    action_wants[unit_id][action_key] = ACTION_WANTED
                elif "goto" in action_key:
                    action_wants[unit_id][action_key] = ACTION_WANTED*random()*0.25
                elif action_key == "build":
                    action_wants[unit_id][action_key] = ACTION_WANTED*random()*0.75
                else:
                    action_wants[unit_id][action_key] = ACTION_UNWANTED
        return action_wants

    def calculate_city_actions(self):
        a_options = self._turn_opts["city"]
        action_wants = {}
        for city_id in a_options.get_actors():
            action_wants[city_id] = {}
            actions = a_options.get_actions(city_id, valid_only=True)
            for action_key in actions:
                if actions[action_key] is None:
                    continue
                if "change_improve_prod" in action_key:
                    action_wants[city_id][action_key] = ACTION_WANTED*random()*0.75
                if "change_unit_prod" in action_key:
                    action_wants[city_id][action_key] = ACTION_WANTED*random()*0.25
                else:
                    action_wants[city_id][action_key] = ACTION_UNWANTED
        return action_wants


my_bot = SimpleBot()
my_civ_controller = CivController(my_bot, "chrisrocks", visualize=False)
CivConnection(my_civ_controller, 'http://localhost')
