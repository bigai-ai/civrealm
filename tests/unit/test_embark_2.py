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
    controller.set_parameter('debug.load_game', 'testcontroller_T173_embark')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_embark_2(controller):
    fc_logger.info("test_embark_2")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    unit_id = 284
    # for unit_id in unit_opt.unit_data.keys():
    unit_focus = unit_opt.unit_data[unit_id]
    ptile = unit_focus.ptile

    print(
        f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, unit_focus.punit)}, activity: {unit_focus.punit['activity']}.")

    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
    print('Embark')
    # Perform embark action
    valid_actions[f'embark_{map_const.DIR8_NORTHEAST}_637'].trigger_action(controller.ws_client)
    # The unit's original position is 431
    assert (ptile['index'] == 431)

    # Get updated state
    controller.get_info_and_observation()
    boat_id = 637
    boat_focus = unit_opt.unit_data[boat_id]
    boat_tile = boat_focus.ptile

    # Get unit's new position
    ptile = unit_focus.ptile
    assert (ptile['index'] != 431)
    # Unit is now on the boat
    assert (ptile['index'] == boat_tile['index'])


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T173_embark')
    test_embark_2(controller)


if __name__ == '__main__':
    main()
