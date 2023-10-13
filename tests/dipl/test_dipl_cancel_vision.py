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


def test_dipl_cancel_vision(controller):
    fc_logger.info("test_dipl_cancel_vision")
    _, options = get_first_observation_option(controller)

    player_opt = options['dipl']
    cancel_vision_act = find_keys_with_keyword(player_opt.get_actions(4, valid_only=True), 'cancel_vision')[0]

    assert (cancel_vision_act.is_action_valid())
    vs_1 = player_opt.players[0]['gives_shared_vision'][4]

    cancel_vision_act.trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    vs_2 = player_opt.players[0]['gives_shared_vision'][4]

    assert (vs_1 == 1 and vs_2 == 0)
