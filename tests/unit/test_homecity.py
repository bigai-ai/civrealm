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
import freeciv_gym.freeciv.units.unit_helpers as unit_helpers
from freeciv_gym.freeciv.civ_controller import CivController
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option
import freeciv_gym.freeciv.map.map_const as map_const
import freeciv_gym.freeciv.utils.fc_types as fc_types


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T53_2023-07-27-02_29_homecity')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_homecity(controller):
    fc_logger.info("test_homecity")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_id = 158
    unit_opt = options['unit']
    unit_focus = unit_opt.unit_data[unit_id]
    punit = unit_opt.unit_ctrl.units[unit_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    assert ('set_homecity' in valid_actions.keys())
    assert (len(valid_actions) > 0)
    unit_focus = unit_opt.unit_data[unit_id]
    # Check whether the action pro is accurate
    assert (unit_focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_HOME_CITY] == {'min': 200, 'max': 200})
    # Go to north
    valid_actions[f'goto_{map_const.DIR8_NORTH}'].trigger_action(controller.ws_client)
    controller.send_end_turn()
    controller.get_info_and_observation()
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # The unit is not in the city tile, cannot change home city.
    assert ('set_homecity' not in valid_actions.keys())
    assert (unit_focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_HOME_CITY] == {'min': 0, 'max': 0})
    # Go back to city tile
    valid_actions[f'goto_{map_const.DIR8_SOUTH}'].trigger_action(controller.ws_client)
    controller.send_end_turn()
    controller.get_info_and_observation()
    assert (unit_focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_HOME_CITY] == {'min': 200, 'max': 200})
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    unit_action = valid_actions['set_homecity']
    print(
        f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}, home city: {punit['homecity']}.")
    assert (unit_action.is_action_valid())
    unit_action.trigger_action(controller.ws_client)
    print(f"Change the homecity of unit {unit_id} to the current garissoned city")
    controller.send_end_turn()
    controller.get_info_and_observation()
    punit = unit_opt.unit_ctrl.units[unit_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    print(
        f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}, home city: {punit['homecity']}.")

    unit_id = 248
    unit_focus = unit_opt.unit_data[unit_id]
    punit = unit_opt.unit_ctrl.units[unit_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # The unit's homecity is the current city, cannot change home city here.
    assert ('set_homecity' not in valid_actions.keys())
    assert (len(valid_actions) > 0)
    assert (unit_focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_HOME_CITY] == {'min': 0, 'max': 0})
    print(
        f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}, home city: {punit['homecity']}.")


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T53_2023-07-27-02_29_homecity')
    test_homecity(controller)


if __name__ == '__main__':
    main()
