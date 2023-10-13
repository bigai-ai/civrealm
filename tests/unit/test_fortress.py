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
import civrealm.freeciv.units.unit_helpers as unit_helpers
from civrealm.freeciv.civ_controller import CivController
from civrealm.freeciv.utils.fc_types import EXTRA_FORTRESS
import civrealm.freeciv.map.map_const as map_const
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T133_2023-07-20-15_23_diplcity')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_fortress(controller):
    fc_logger.info("test_fortress")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    build_action = None
    worker_id = 535
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    build_action = valid_actions['fortress']
    punit = unit_opt.unit_ctrl.units[worker_id]
    build_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    print(
        f"Unit id: {worker_id}, position: ({build_tile['x']}, {build_tile['y']}), extras[EXTRA_FORTRESS]: {build_tile['extras'][EXTRA_FORTRESS]}, move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    assert (not (build_tile['extras'][EXTRA_FORTRESS] == 1))
    # The unit has move in this turn, the fortress should be valid
    assert (build_action.is_action_valid())
    # Trigger fortress action will change the activity state of the unit.
    build_action.trigger_action(controller.ws_client)
    # Get unit new info
    controller.get_info_and_observation()
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    # Already performing fortress, the fortress action should be invalid.
    assert ('fortress' not in valid_actions)
    # Building fortress will make activity_tgt become 7.
    print(punit)
    print('Begin building a fortress, needs a few turns to finish ...')
    # Wait for 3 turns (until job is done)
    for turn_i in range(3):
        controller.send_end_turn()
        controller.get_info_and_observation()
    # Get updated state
    print(
        f"Unit id: {worker_id}, position: ({build_tile['x']}, {build_tile['y']}), extras[EXTRA_FORTRESS]: {build_tile['extras'][EXTRA_FORTRESS]}, move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    assert (build_tile['extras'][EXTRA_FORTRESS] == 1)

    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    # There is already a fortress extra, the fortress action should be invalid
    assert ('fortress' not in valid_actions)
    # The pillage action should be valid
    assert ('pillage' in valid_actions)
    print(valid_actions.keys())

    # Check another unit
    unit_id = 625
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    unit_focus = unit_opt.unit_data[unit_id]
    ptile = unit_focus.ptile
    # The tile has no fortress extra.
    assert (ptile['extras'][EXTRA_FORTRESS] == 0)
    # This unit type cannot perform fortress action.
    assert ('fortress' not in valid_actions)
    print(valid_actions.keys())


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T133_2023-07-20-15_23_diplcity')
    test_fortress(controller)


if __name__ == '__main__':
    main()
