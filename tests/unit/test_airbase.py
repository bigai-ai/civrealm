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
from civrealm.freeciv.utils.fc_types import EXTRA_AIRBASE, EXTRA_FORTRESS
import civrealm.freeciv.map.map_const as map_const
import civrealm.freeciv.units.unit_helpers as unit_helpers
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T370_2023-08-01-06_00')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_airbase(controller):
    fc_logger.info("test_airbase")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    unit_id = 843
    punit = unit_opt.unit_ctrl.units[unit_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    # print(unit_opt.unit_ctrl.units[801])
    # print(unit_opt.unit_ctrl.units[776])
    # print(unit_opt.unit_ctrl.units[479])
    # print(unit_opt.unit_ctrl.units[475])
    # print(unit_opt.unit_ctrl.units[467])
    print(
        f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    # Get valid actions
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    assert ('airbase' in valid_actions)
    # Choose airbase action
    valid_actions['airbase'].trigger_action(controller.ws_client)
    print(f"Activity: {punit['activity']}")
    controller.get_info_and_observation()
    print(f"Activity: {punit['activity']}")
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # Already performing airbase. The airbase action is invalid.
    assert ('airbase' not in valid_actions)
    assert (unit_tile['extras'][EXTRA_AIRBASE] == 0)
    print(f'valid action keys: {valid_actions.keys()}')
    # Building airbase will make activity_tgt become 8.
    print(punit)
    # Wait for airbase finish.
    for _ in range(3):
        controller.send_end_turn()
        controller.get_info_and_observation()
    print('Airbase built')

    assert (unit_tile['extras'][EXTRA_AIRBASE] == 1)
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # Already has airbase, cannot build again
    assert ('airbase' not in valid_actions)
    print(f'valid action keys: {valid_actions.keys()}')

    # Start to build fortress
    valid_actions['fortress'].trigger_action(controller.ws_client)
    print(f"Activity: {punit['activity']}")
    controller.get_info_and_observation()
    print(f"Activity: {punit['activity']}")
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    assert ('fortress' not in valid_actions)
    assert (unit_tile['extras'][EXTRA_FORTRESS] == 0)
    assert ('airbase' not in valid_actions)
    print(f'valid action keys: {valid_actions.keys()}')

    # Wait for fortress finish.
    for _ in range(3):
        controller.send_end_turn()
        controller.get_info_and_observation()
    print('fortress built')

    assert (unit_tile['extras'][EXTRA_AIRBASE] == 1)
    assert (unit_tile['extras'][EXTRA_FORTRESS] == 1)
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # Has both fortress and airbase, cannot build airbase again.
    assert ('airbase' not in valid_actions)
    assert ('fortress' not in valid_actions)
    print(f'valid action keys: {valid_actions.keys()}')


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T370_2023-08-01-06_00')
    test_airbase(controller)


if __name__ == '__main__':
    main()
