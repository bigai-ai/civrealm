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
import civrealm.freeciv.units.unit_helpers as unit_helpers
from civrealm.freeciv.utils.fc_types import EXTRA_POLLUTION
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


def test_pollution(controller):
    fc_logger.info("test_pollution")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    worker_ids = [468, 564]
    for unit_id in worker_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 468:
            # assert (terrain['pollution_time'] == 0 and 'pollution' not in valid_actions)
            assert ('pollution' not in valid_actions.keys())
        if unit_id == 564:
            assert (unit_tile['extras'][EXTRA_POLLUTION] == 1)
            assert ('pollution' in valid_actions.keys())
            valid_actions[f'pollution'].trigger_action(controller.ws_client)

    # Wait for 5 turns to finish pollution
    for _ in range(5):
        controller.send_end_turn()
        controller.get_info_and_observation()

    unit_id = 564
    punit = unit_opt.unit_ctrl.units[unit_id]
    clean_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    # Pollution has been removed.
    assert (not clean_tile['extras'][EXTRA_POLLUTION] == 1)
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    assert ('pollution' not in valid_actions.keys())


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T257_2023-08-07-14_04')
    test_pollution(controller)


if __name__ == '__main__':
    main()
