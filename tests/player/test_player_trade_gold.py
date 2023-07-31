# # Copyright (C) 2023  The Freeciv-gym project
# #
# # This program is free software: you can redistribute it and/or modify it
# # under the terms of the GNU General Public License as published by the Free
# #  Software Foundation, either version 3 of the License, or (at your option)
# # any later version.
# #
# # This program is distributed in the hope that it will be useful, but
# # WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# # or FITNESS FOR A PARsrc/freeciv_gym/configs/default_setting.ymlTICULAR PURPOSE.  See the GNU General Public License for more details.
# #
# # You should have received a copy of the GNU General Public License along
# # with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest
import random
from freeciv_gym.freeciv.civ_controller import CivController
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option
import freeciv_gym.freeciv.players.player_const as player_const

@pytest.fixture
def controller():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T169_2023-07-27-05_01')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def find_keys_with_keyword(dictionary, keyword):
    keys = []
    for key in dictionary:
        if keyword in key:
            keys.append(dictionary[key])
    return keys


def test_player_trade_gold(controller):
    fc_logger.info("test_player_trade_gold")
    _, options = get_first_observation_option(controller)

    player_opt = options['player']
    trade_gold_act = find_keys_with_keyword(player_opt._action_dict[3], 'trade_gold_clause')[0]

    assert (trade_gold_act.is_action_valid())
    clauses = controller.controller_list['dipl'].diplomacy_clause_map[3]
    len_1 = len(clauses)

    trade_gold_act.trigger_action(controller.ws_client)
    controller.send_end_turn()
    controller.get_observation()
    clauses = controller.controller_list['dipl'].diplomacy_clause_map[3]
    len_2 = len(clauses)

    assert (len_1 + 1 == len_2 and clauses[0]['type'] == player_const.CLAUSE_GOLD)