# Copyright (C) 2023  The Freeciv-gym project
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
from freeciv_gym.freeciv.civ_controller import CivController
from freeciv_gym.freeciv.utils.fc_types import EXTRA_ROAD, EXTRA_IRRIGATION
import freeciv_gym.freeciv.map.map_const as map_const
import freeciv_gym.freeciv.units.unit_helpers as unit_helpers
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T71_pillage')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_pillage(controller):
    fc_logger.info("test_pillage")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    worker_id = [138, 139, 269]
    for unit_id in unit_opt.unit_ctrl.units.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)

    for worker in worker_id:
        valid_actions = unit_opt.get_actions(worker, valid_only=True)
        # pillage is valid for all works
        assert ('pillage' in valid_actions)
        if worker == 138:
            # Trigger pillage action for 138 worker
            valid_actions['pillage'].trigger_action(controller.ws_client)

    # Update state
    controller.get_info_and_observation()
    worker_id = [139, 269]

    for worker in worker_id:
        valid_actions = unit_opt.get_actions(worker, valid_only=True)
        # pillage is valid for all works
        assert ('pillage' in valid_actions)
        if worker == 139:
            # Trigger pillage action for 138 worker
            valid_actions['pillage'].trigger_action(controller.ws_client)

    # Update state
    controller.get_info_and_observation()
    worker_id = 269

    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    # The current tile has two extras and there are already two workers are doing pillage, so pillage is not valid for the remaining worker.
    assert ('pillage' not in valid_actions)

    unit_opt = options['unit']
    punit = unit_opt.unit_ctrl.units[worker_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])

    # Currently has two extras
    assert (unit_tile['extras'][EXTRA_ROAD] == 1)
    assert (unit_tile['extras'][EXTRA_IRRIGATION] == 1)

    print('Begin pillaging, needs one turn to finish ...')
    controller.send_end_turn()
    controller.get_info_and_observation()

    # Pillage remove extras
    assert (not (unit_tile['extras'][EXTRA_ROAD] == 1))
    assert (not (unit_tile['extras'][EXTRA_IRRIGATION] == 1))


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T71_pillage')
    test_pillage(controller)


if __name__ == '__main__':
    main()
