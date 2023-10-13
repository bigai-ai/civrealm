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


def test_disband(controller):
    fc_logger.info("test_disband")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_id = 138
    unit_opt = options['unit']
    assert (unit_id in unit_opt.unit_ctrl.units.keys())
    punit = unit_opt.unit_ctrl.units[unit_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    unit_action = valid_actions['disband']
    print(
        f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    assert (unit_action.is_action_valid())
    unit_action.trigger_action(controller.ws_client)
    print(f"Disband unit {unit_id}")
    for turn_i in range(1):
        controller.send_end_turn()
        options = controller.turn_manager.turn_actions
        controller.get_info_and_observation()
    unit_opt = options['unit']
    assert not (unit_id in unit_opt.unit_ctrl.units.keys())


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    test_disband(controller)


if __name__ == '__main__':
    main()
