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

    if len(keys) == 1:
        return keys[0]
    else:
        return keys


def test_city_change_specialist(controller):

    # ============================== ensure at least 1 specialist ==============================
    controller.init_network()
    controller.get_observation()
    options = controller.turn_manager.get_available_actions()

    city_opt = options['city']

    city_id = 155
    pcity = city_opt.cities[city_id]

    valid_unwork_actions = find_keys_with_keyword(city_opt._action_dict[city_id], 'city_unwork')
    unwork_action = random.choice(valid_unwork_actions)

    assert (unwork_action.is_action_valid())
    dx = unwork_action.dx
    dy = unwork_action.dy

    ctile = city_opt.city_map.map_ctrl.city_tile(pcity)
    wtile = city_opt.city_map.map_ctrl.map_pos_to_tile(ctile["x"] + dx, ctile["y"] + dy)
    if_work_1 = wtile["worked"]

    unwork_action.trigger_action(controller.ws_client)
    controller.get_observation()
    if_work_2 = wtile["worked"]

    assert (if_work_1 == city_id and if_work_2 == 0)

    # ===================================== test city_work =====================================
    options = controller.turn_manager.get_available_actions()
    city_opt = options['city']
    pcity = city_opt.cities[city_id]

    change_specialist_action = find_keys_with_keyword(city_opt._action_dict[city_id], 'city_change_specialist_0')
    assert (change_specialist_action.is_action_valid())

    specialists_1 = pcity['specialists']

    change_specialist_action.trigger_action(controller.ws_client)
    controller.get_observation()
    specialists_2 = pcity['specialists']

    assert (specialists_1[0] == 1 and specialists_1[1] == 0 and specialists_1[2] == 0 and
            specialists_2[0] == 0 and specialists_2[1] == 1 and specialists_2[2] == 0)

