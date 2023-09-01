# Copyright (C) 2023  The Freeciv-gym project
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

import pytest
import random
from freeciv_gym.freeciv.civ_controller import CivController
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option


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


def test_city_change_improve_prod(controller):
    fc_logger.info("test_city_change_improvement_prod")
    _, options = get_first_observation_option(controller)

    city_opt = options['city']

    for city_id in city_opt.cities.keys():
        pcity = city_opt.cities[city_id]

        valid_improve_prod_actions = find_keys_with_keyword(city_opt.get_actions(city_id, valid_only=True),
                                                            'change_improve_prod')
        if len(valid_improve_prod_actions) == 0:
            continue

        improve_prod_action = random.choice(valid_improve_prod_actions)
        assert (improve_prod_action.is_action_valid())

        prod_kind_1 = pcity['production_kind']

        improve_prod_action.trigger_action(controller.ws_client)
        controller.send_end_turn()
        controller.get_info_and_observation()
        prod_kind_2 = pcity['production_kind']

        assert (prod_kind_1 != prod_kind_2)
