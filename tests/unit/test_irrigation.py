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
from civrealm.freeciv.utils.fc_types import EXTRA_IRRIGATION
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_irrigation(controller):
    fc_logger.info("test_irrigation")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    worker_id = 138
    for unit_id in unit_opt.unit_ctrl.units.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        # Get valid actions
        if unit_id == worker_id:
            valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
            test_action_list.append(valid_actions[f'goto_{map_const.DIR8_WEST}'])
            print(valid_actions.keys())
            # There is no river or irrigated area nearby, the irrigation action is invalid.
            assert ('irrigation' not in valid_actions)

    print('Move to the west tile which is near the sea (irrigation is allowed)')
    # Perform goto action for the worker
    for action in test_action_list:
        action.trigger_action(controller.ws_client)
    # Get unit new state
    controller.get_info_and_observation()
    punit = unit_opt.unit_ctrl.units[worker_id]
    build_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    assert (not (build_tile['extras'][EXTRA_IRRIGATION] == 1))
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    # The unit has no move left, the build should be invalid
    assert ('irrigation' not in valid_actions)

    # End turn
    controller.send_end_turn()
    controller.get_info_and_observation()
    print(
        f"Unit id: {worker_id}, position: ({build_tile['x']}, {build_tile['y']}), extras[EXTRA_IRRIGATION]: {build_tile['extras'][EXTRA_IRRIGATION]}, move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    # The unit has move in new turn, the build should be valid
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    irrigation_action = valid_actions['irrigation']
    assert (irrigation_action.is_action_valid())
    irrigation_action.trigger_action(controller.ws_client)
    print('Begin building a irrigation, needs a few turns to finish ...')
    # Wait for 5 turns (until the work is done)
    for _ in range(5):
        controller.send_end_turn()
        controller.get_info_and_observation()
    # Get updated state
    print(
        f"Unit id: {worker_id}, position: ({build_tile['x']}, {build_tile['y']}), extras[EXTRA_IRRIGATION]: {build_tile['extras'][EXTRA_IRRIGATION]}, move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    assert (build_tile['extras'][EXTRA_IRRIGATION] == 1)

    # Move back to the original position where the irrigation action was invalid
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    valid_actions[f'goto_{map_const.DIR8_EAST}'].trigger_action(controller.ws_client)
    controller.send_end_turn()
    controller.get_info_and_observation()
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    # There is an irrigated area in the west, the irrigation action becomes valid.
    assert ('irrigation' in valid_actions)
    print(valid_actions.keys())
    build_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    assert (build_tile['extras'][EXTRA_IRRIGATION] == 0)
    print(
        f"Unit id: {worker_id}, position: ({build_tile['x']}, {build_tile['y']}), extras[EXTRA_IRRIGATION]: {build_tile['extras'][EXTRA_IRRIGATION]}, move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    # Start irrigating
    valid_actions['irrigation'].trigger_action(controller.ws_client)
    print('Begin building a irrigation, needs a few turns to finish ...')
    # Wait for 5 turns (until the work is done)
    for _ in range(5):
        controller.send_end_turn()
        controller.get_info_and_observation()
    print(
        f"Unit id: {worker_id}, position: ({build_tile['x']}, {build_tile['y']}), extras[EXTRA_IRRIGATION]: {build_tile['extras'][EXTRA_IRRIGATION]}, move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    assert (build_tile['extras'][EXTRA_IRRIGATION] == 1)


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    test_irrigation(controller)


if __name__ == '__main__':
    main()
