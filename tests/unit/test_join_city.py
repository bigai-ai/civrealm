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
from civrealm.freeciv.civ_controller import CivController
import civrealm.freeciv.map.map_const as map_const
import civrealm.freeciv.units.unit_helpers as unit_helpers
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option
import civrealm.freeciv.utils.fc_types as fc_types


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T52_join_city')
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
    unit_id = 219
    unit_focus = unit_opt.unit_data[unit_id]
    ptile = unit_focus.ptile
    print(
        f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, unit_focus.punit)}.")
    # The settler is not inside a city, cannot join
    assert (unit_focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_JOIN_CITY] == {'min': 0, 'max': 0})
    # Get valid actions
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    assert ('join_city' not in valid_actions)
    # Move to south
    valid_actions[f'goto_{map_const.DIR8_SOUTH}'].trigger_action(controller.ws_client)

    controller.send_end_turn()
    # Get unit new state
    controller.get_info_and_observation()
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # Start a plant activity
    valid_actions['plant'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()

    options = controller.turn_manager.turn_actions
    unit_focus = unit_opt.unit_data[unit_id]
    ptile = unit_focus.ptile
    print(
        f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, unit_focus.punit)}, activity: {unit_focus.punit['activity']}.")
    # The settler can join city now.
    assert (unit_focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_JOIN_CITY] == {'min': 200, 'max': 200})
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    join_action = valid_actions['join_city']

    # The unit has move in new turn, the join should be valid
    assert (join_action.is_action_valid())
    join_action.trigger_action(controller.ws_client)
    print('trigger join action')
    # Get unit new state
    controller.get_info_and_observation()
    # After join city, the unit is removed.
    assert (219 not in unit_opt.unit_ctrl.units.keys())
