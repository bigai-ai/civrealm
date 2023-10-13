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


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T134_sabotage')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_spy_sabotage(controller):
    fc_logger.info("test_spy_sabotage")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    diplomat_id = 915

    punit = unit_opt.unit_ctrl.units[diplomat_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    print(
        f"Unit id: {diplomat_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}, activity: {punit['activity']}.")
    # Get valid actions
    valid_actions = unit_opt.get_actions(diplomat_id, valid_only=True)
    print(valid_actions.keys())
    valid_actions['fortify'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    print(f"Participate in activity {punit['activity']}")

    valid_actions = unit_opt.get_actions(diplomat_id, valid_only=True)
    test_action_list.append(valid_actions[f'spy_sabotage_city_{map_const.DIR8_SOUTHWEST}'])

    print('Sabotage the city on southwest tile')
    # Perform spy_sabotage action of the diplomat
    for action in test_action_list:
        action.trigger_action(controller.ws_client)
    # Get unit new state
    # controller.send_end_turn()
    controller.get_info_and_observation()
    options = controller.turn_manager.turn_actions
    unit_opt = options['unit']
    # The diplomat should have been consumed
    assert not (diplomat_id in unit_opt.unit_ctrl.units.keys())


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T134_sabotage')
    test_spy_sabotage(controller)


if __name__ == '__main__':
    main()
