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
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option
from civrealm.freeciv.utils.fc_types import ACTIVITY_FORTIFIED, ACTIVITY_FORTIFYING, ACTION_UNIT_MOVE


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_fortify(controller):
    fc_logger.info("test_fortify")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_id = 185
    unit_opt = options['unit']
    punit = unit_opt.unit_ctrl.units[unit_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    print(
        f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    assert ('fortify' in valid_actions.keys() and not punit['activity'] == ACTIVITY_FORTIFIED)
    unit_action = valid_actions['fortify']
    assert (unit_action.is_action_valid())
    # Perform fortify action
    unit_action.trigger_action(controller.ws_client)
    print(f"Fortify unit {unit_id}")
    # Get unit info after the performed action
    controller.get_info_and_observation()
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    print(valid_actions.keys())
    punit = unit_opt.unit_ctrl.units[unit_id]
    print(punit)
    # Unit activity is FORTIFYING in the same turn
    assert (punit['activity'] == ACTIVITY_FORTIFYING)

    # End the turn
    controller.send_end_turn()
    controller.get_info_and_observation()
    punit = unit_opt.unit_ctrl.units[unit_id]
    # Unit activity becomes to FORTIFIED in the next turn
    assert (punit['activity'] == ACTIVITY_FORTIFIED)
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    assert ('fortify' not in valid_actions.keys())
    print(valid_actions.keys())
    print(punit)
    # When a unit has activity, the move pro get from server is 0 even the unit still has move.
    # print(unit_opt.unit_data[unit_id].action_prob[4][ACTION_UNIT_MOVE])


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    test_fortify(controller)


if __name__ == '__main__':
    main()
