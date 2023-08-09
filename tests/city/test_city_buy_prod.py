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
from freeciv_gym.freeciv.utils.fc_types import VUT_UTYPE, VUT_IMPROVEMENT

@pytest.fixture
def controller():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-20-05_37')
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


def test_city_buy_prod(controller):
    fc_logger.info("test_city_buy_prod")
    _, options = get_first_observation_option(controller)

    city_opt = options['city']

    for city_id in city_opt.cities.keys():
        pcity = city_opt.cities[city_id]

        valid_city_buy_actions = find_keys_with_keyword(city_opt.get_actions(city_id, valid_only=True),
                                                        'city_buy_production')
        if len(valid_city_buy_actions) == 0:
            continue

        city_buy_action = random.choice(valid_city_buy_actions)
        assert (city_buy_action.is_action_valid())

        if city_buy_action.kind == VUT_UTYPE:
            continue
        improvement_1 = pcity['improvements'][city_buy_action.value]

        city_buy_action.trigger_action(controller.ws_client)
        controller.send_end_turn()
        controller.get_observation()

        improvement_2 = pcity['improvements'][city_buy_action.value]

        assert (improvement_1 == 0 and improvement_2 == 1)
