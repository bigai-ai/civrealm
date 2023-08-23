# # Copyright (C) 2023  The Freeciv-gym project
# #
# # This program is free software: you can redistribute it and/or modify it
# # under the terms of the GNU General Public License as published by the Free
# # Software Foundation, either version 3 of the License, or (at your option)
# # any later version.
# #
# # This program is distributed in the hope that it will be useful, but
# # WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# # or FITNESS FOR A PARsrc/freeciv_gym/configs/default_setting.ymlTICULAR PURPOSE.  See the GNU General Public License
# for more details.
# #
# # You should have received a copy of the GNU General Public License along
# # with this program.  If not, see <http://www.gnu.org/licenses/>.


import pytest
from freeciv_gym.freeciv.civ_controller import CivController
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option
import freeciv_gym.freeciv.utils.fc_types as fc_types
# def is_port_in_use(port: int) -> bool:
#     import socket
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#         return s.connect_ex(('localhost', port)) == 0


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T52_2023-07-26-02_14')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()
    # fc_logger.info(f'Port 8080 in use: {is_port_in_use(8080)}')
    # fc_logger.info(f"Port {fc_args['client_port']} in use: {is_port_in_use(fc_args['client_port'])}")


def test_join_city(controller):
    fc_logger.info("test_join_city")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    join_action = None

    for unit_id in unit_opt.unit_ctrl.units.keys():
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        print(
            f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(unit_focus.punit)}.")
        if unit_id == 219:
            # The settler is not inside a city, cannot join
            assert (unit_focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_JOIN_CITY] == {'min': 0, 'max': 0})
            # Get valid actions
            valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
            assert ('join' not in valid_actions)
            # Move to south
            valid_actions[f'goto_{map_const.DIR8_SOUTH}'].trigger_action(controller.ws_client)

    controller.send_end_turn()
    # Get unit new state
    options = controller.get_info()['available_actions']
    controller.get_observation()
    for unit_id in unit_opt.unit_ctrl.units.keys():
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        print(
            f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(unit_focus.punit)}.")
        if unit_id == 219:
            # The settler can build city now.
            assert (unit_focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_JOIN_CITY] == {'min': 200, 'max': 200})
            valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
            join_action = valid_actions['join']

    # The unit has move in new turn, the build should be valid
    assert (join_action.is_action_valid())
    join_action.trigger_action(controller.ws_client)
    fc_logger.info('trigger join action')
    # # Get unit new state
    controller.get_observation()
    # After join city, the unit is removed.
    assert (219 not in unit_opt.unit_ctrl.units.keys())
