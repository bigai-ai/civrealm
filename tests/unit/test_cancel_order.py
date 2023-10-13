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
from civrealm.freeciv.utils.fc_types import ACTIVITY_FORTIFIED, ACTIVITY_FORTIFYING, ACTION_UNIT_MOVE, ACTIVITY_IDLE


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_cancel_order(controller):
    fc_logger.info("test_cancel_order")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_ids = [139, 185]
    unit_opt = options['unit']
    for unit_id in unit_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 139:
            # Move to north
            valid_actions[f'goto_{map_const.DIR8_NORTH}'].trigger_action(controller.ws_client)
        if unit_id == 185:
            # Fortify
            print(f'unit_id: {unit_id} do fortify.')
            valid_actions['fortify'].trigger_action(controller.ws_client)

    controller.get_info_and_observation()
    for unit_id in unit_ids:
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 139:
            # The unit has not move. It also has no activity.
            assert ('cancel_order' not in valid_actions)
            print(f'unit_id: {unit_id}, valid_actions: {valid_actions.keys()}')
        if unit_id == 185:
            # This unit has an activity, can cancel the order.
            assert ('cancel_order' in valid_actions)
            print(f'unit_id: {unit_id}, valid_actions: {valid_actions.keys()}')

    # End the turn
    print('End Turn')
    controller.send_end_turn()
    controller.get_info_and_observation()
    for unit_id in unit_ids:
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 139:
            assert ('cancel_order' not in valid_actions)
            # Irrigate
            print(f'unit_id: {unit_id} do irrigate.')
            valid_actions['irrigation'].trigger_action(controller.ws_client)
        if unit_id == 185:
            punit = unit_opt.unit_ctrl.units[unit_id]
            # Unit activity becomes to FORTIFIED in the next turn
            assert (punit['activity'] != ACTIVITY_IDLE)
            # Cancel the current order
            print(f'unit_id: {unit_id} cancel order.')
            valid_actions['cancel_order'].trigger_action(controller.ws_client)

    controller.get_info_and_observation()
    for unit_id in unit_ids:
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 139:
            assert ('cancel_order' in valid_actions)
            print(f'unit_id: {unit_id}, valid_actions: {valid_actions.keys()}')
            # When a unit has activity, the move pro get from server is 0 even the unit still has move.
            print(unit_opt.unit_data[unit_id].action_prob[4][ACTION_UNIT_MOVE])
            # Change irrigation activity to mine
            # print(f'unit_id: {unit_id} do mine.')
            # valid_actions['mine'].trigger_action(controller.ws_client)
            # TODO: if comment out the below two lines, the test will become very slow. Figure out why.
            print(f'unit_id: {unit_id} cancel order.')
            valid_actions['cancel_order'].trigger_action(controller.ws_client)
        if unit_id == 185:
            punit = unit_opt.unit_ctrl.units[unit_id]
            # Unit activity becomes to FORTIFIED in the next turn
            assert (punit['activity'] == ACTIVITY_IDLE)
            assert ('cancel_order' not in valid_actions)
            print(f'unit_id: {unit_id}, valid_actions: {valid_actions.keys()}')

    controller.get_info_and_observation()
    unit_id = 139
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    print(f'unit_id: {unit_id}, valid_actions: {valid_actions.keys()}')
    # Change activity to road
    print(f'unit_id: {unit_id} do road.')
    valid_actions['build_road'].trigger_action(controller.ws_client)

    controller.get_info_and_observation()
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    print(f'unit_id: {unit_id}, valid_actions: {valid_actions.keys()}')
    # Cancel order
    print(f'unit_id: {unit_id} cancel order.')
    valid_actions['cancel_order'].trigger_action(controller.ws_client)

    controller.get_info_and_observation()
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    print(f'unit_id: {unit_id}, valid_actions: {valid_actions.keys()}')


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    test_cancel_order(controller)


if __name__ == '__main__':
    main()
