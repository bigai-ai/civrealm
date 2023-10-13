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
    controller = CivController('testcontroller')
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


def test_gov_decrease_tax(controller):
    fc_logger.info("test_gov_decrease_tax")
    _, options = get_first_observation_option(controller)

    player_opt = options['player']
    pplayer = player_opt.players[0]

    decrease_tax_action_set = find_keys_with_keyword(player_opt.get_actions(0, valid_only=True),
                                                     'decrease_tax')
    if len(decrease_tax_action_set) > 0:
        decrease_tax_action = decrease_tax_action_set[0]

        assert (decrease_tax_action.is_action_valid())

        tax_1 = pplayer['tax']

        decrease_tax_action.trigger_action(controller.ws_client)
        controller.get_info_and_observation()
        tax_2 = pplayer['tax']

        assert (tax_1 - tax_2 == 10)
