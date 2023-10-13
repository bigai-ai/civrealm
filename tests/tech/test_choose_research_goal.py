# Copyright (C) 2023  The CivRealm project
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

import pytest
import random
from civrealm.freeciv.civ_controller import CivController
import civrealm.freeciv.map.map_const as map_const
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def find_keys_with_keyword(dictionary, keyword):
    keys = []
    for key in dictionary:
        if keyword in key:
            keys.append(dictionary[key])
    return keys


def test_choose_research_goal(controller):
    fc_logger.info("test_city_unwork")
    _, options = get_first_observation_option(controller)

    tech_opt = options['tech']

    valid_tech_goal_actions = find_keys_with_keyword(tech_opt.get_actions('cur_player', valid_only=True),
                                                     'set_tech_goal')
    tech_goal_action = random.choice(valid_tech_goal_actions)
    assert (tech_goal_action.is_action_valid())

    tech_data = tech_opt.player_ctrl.research_data
    tech_1 = tech_data[tech_opt.player_ctrl.my_player_id]['tech_goal']

    tech_goal_action.trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    tech_2 = tech_data[tech_opt.player_ctrl.my_player_id]['tech_goal']

    assert (tech_1 != tech_2)
