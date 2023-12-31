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
from civrealm.freeciv.utils.fc_types import EXTRA_MINE
import civrealm.freeciv.map.map_const as map_const
import civrealm.freeciv.units.unit_helpers as unit_helpers
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_mine')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_mine(controller):
    fc_logger.info("test_mine")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    build_action = None
    worker_id = 139
    for unit_id in unit_opt.unit_ctrl.units.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == worker_id:
            test_action_list.append(
                valid_actions[f'goto_{map_const.DIR8_NORTH}'])
            build_action = valid_actions['mine']
        else:
            pass
    print('Move to the north tile which has a hill (mine is allowed)')
    # Perform goto action for the worker
    for action in test_action_list:
        action.trigger_action(controller.ws_client)
    # Get unit new state
    controller.get_info_and_observation()
    punit = unit_opt.unit_ctrl.units[worker_id]
    build_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    # The unit has no move left, the build should be invalid
    assert (not build_action.is_action_valid())
    # End turn
    controller.send_end_turn()
    controller.get_info_and_observation()
    print(
        f"Unit id: {worker_id}, position: ({build_tile['x']}, {build_tile['y']}), extras[EXTRA_MINE]: {build_tile['extras'][EXTRA_MINE]}, move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")

    # Perform irrigation activity first. This is to test whether mine action will cancel the irrigation activity first.
    print('Perform irrigation activity first')
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    valid_actions['irrigation'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()

    # The unit has move in new turn, the build should be valid
    assert (not (build_tile['extras'][EXTRA_MINE] == 1))
    assert (build_action.is_action_valid())
    build_action.trigger_action(controller.ws_client)
    print('Begin building a mine, needs a few turns to finish ...')
    print(punit['activity'])
    controller.get_info_and_observation()
    print(punit['activity'])
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    print(f'valid_actions: {valid_actions.keys()}')
    # Wait for 15 turns (until the work is done)
    for turn_i in range(15):
        controller.send_end_turn()
        controller.get_info_and_observation()
    # Get updated state
    print(
        f"Unit id: {worker_id}, position: ({build_tile['x']}, {build_tile['y']}), extras[EXTRA_MINE]: {build_tile['extras'][EXTRA_MINE]}, move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    assert (build_tile['extras'][EXTRA_MINE] == 1)


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_mine')
    test_mine(controller)


if __name__ == '__main__':
    main()
