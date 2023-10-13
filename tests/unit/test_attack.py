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
    controller.set_parameter('debug.load_game', 'testcontroller_T82_attack')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_attack(controller):
    fc_logger.info("test_attack")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    horseman_id = 250
    punit = unit_opt.unit_ctrl.units[horseman_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    print(
        f"Unit id: {horseman_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}, activity: {punit['activity']}.")
    # Get valid actions
    valid_actions = unit_opt.get_actions(horseman_id, valid_only=True)
    valid_actions['pillage'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    print(f"Participate in activity {punit['activity']}")

    assert (punit['activity'] != 0)

    valid_actions = unit_opt.get_actions(horseman_id, valid_only=True)
    print(valid_actions.keys())
    print('Attack the southeast tile')
    valid_actions[f'attack_{map_const.DIR8_SOUTHEAST}'].trigger_action(controller.ws_client)

    # Get unit new state
    controller.get_info_and_observation()
    unit_opt = controller.turn_manager.turn_actions['unit']
    # The attack leads to the death of unit 250
    assert (250 not in unit_opt.unit_ctrl.units.keys())
