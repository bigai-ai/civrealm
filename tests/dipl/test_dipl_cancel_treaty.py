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
import civrealm.freeciv.players.player_const as player_const


@pytest.fixture
def controller():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T169_2023-07-19-13_11')
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


def test_dipl_cancel_treaty(controller):
    fc_logger.info("test_dipl_cancel_treaty")
    _, options = get_first_observation_option(controller)

    player_opt = options['dipl']
    cancel_treaty_act = find_keys_with_keyword(player_opt.get_actions(4, valid_only=True), 'cancel_treaty')[0]

    assert (cancel_treaty_act.is_action_valid())
    ds_1 = controller.controller_list['dipl'].diplstates[4]

    cancel_treaty_act.trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    ds_2 = controller.controller_list['dipl'].diplstates[4]

    assert (ds_1 == player_const.DS_ALLIANCE and ds_2 == player_const.DS_ARMISTICE)
