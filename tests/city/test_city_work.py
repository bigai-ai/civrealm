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
    controller.set_parameter('debug.load_game', 'testcontroller_T257_2023-08-07-14_04')
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


def test_city_work(controller):
    fc_logger.info("test_city_work")
    _, options = get_first_observation_option(controller)

    city_opt = options['city']

    for city_id in city_opt.cities:
        pcity = city_opt.cities[city_id]

        valid_work_actions = find_keys_with_keyword(city_opt.get_actions(city_id, valid_only=True), 'city_work')
        if len(valid_work_actions) == 0:
            continue

        work_action = random.choice(valid_work_actions)
        assert (work_action.is_action_valid())
        dx = work_action.dx
        dy = work_action.dy

        ctile = city_opt.city_map.map_ctrl.city_tile(pcity)
        wtile = city_opt.city_map.map_ctrl.map_pos_to_tile(ctile["x"] + dx, ctile["y"] + dy)
        if_work_1 = wtile["worked"]

        work_action.trigger_action(controller.ws_client)
        controller.get_info_and_observation()
        if_work_2 = wtile["worked"]

        assert (if_work_1 == 0 and if_work_2 == city_id)
