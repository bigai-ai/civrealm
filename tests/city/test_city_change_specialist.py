# Copyright (C) 2023  The CivRealm project
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
from civrealm.freeciv.civ_controller import CivController
import civrealm.freeciv.map.map_const as map_const
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-27-07_59')
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


def test_city_change_specialist(controller):
    fc_logger.info("test_city_change_specialist")
    _, options = get_first_observation_option(controller)

    city_opt = options['city']

    for city_id in city_opt.cities.keys():
        pcity = city_opt.cities[city_id]

        valid_change_specialist_action = find_keys_with_keyword(city_opt.get_actions(city_id, valid_only=True),
                                                                'city_change_specialist_0')
        if len(valid_change_specialist_action) == 0:
            continue

        change_specialist_action = random.choice(valid_change_specialist_action)
        assert (change_specialist_action.is_action_valid())

        specialists_1 = pcity['specialists']

        change_specialist_action.trigger_action(controller.ws_client)
        controller.get_info_and_observation()
        specialists_2 = pcity['specialists']

        assert (specialists_1[0] == 1 and specialists_1[1] == 0 and specialists_1[2] == 0 and
                specialists_2[0] == 0 and specialists_2[1] == 1 and specialists_2[2] == 0)
