# # Copyright (C) 2023  The Freeciv-gym project
# #
# # This program is free software: you can redistribute it and/or modify it
# # under the terms of the GNU General Public License as published by the Free
# # Software Foundation, either version 3 of the License, or (at your option)
# # any later version.
# #
# # This program is distributed in the hope that it will be useful, but
# # WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# # or FITNESS FOR A PARsrc/freeciv_gym/configs/default_setting.ymlTICULAR PURPOSE.  See the GNU General Public License 
# for more details.
# #
# # You should have received a copy of the GNU General Public License along
# # with this program.  If not, see <http://www.gnu.org/licenses/>.


import pytest
from freeciv_gym.freeciv.civ_controller import CivController
from freeciv_gym.freeciv.game.ruleset import EXTRA_AIRBASE, EXTRA_FORTRESS
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T375_2023-08-02-10_04')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def test_embark(controller):
    fc_logger.info("test_embark")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']

    for unit_id in unit_opt.unit_data.keys():
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        if ptile['x'] == 47 and ptile['y'] == 28:
            print(f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(unit_focus.punit)}.")

    # Plane is in (47, 28)
    plane_id = 1841
    
    valid_actions = unit_opt.get_actions(plane_id, valid_only=True)
    print(f'Unit {plane_id}, valid action keys: {valid_actions.keys()}')
    contain_embark = False
    for action_key in valid_actions:
        if 'embark' in action_key:
            contain_embark = True
            break
    # The unit is a plane, cannot embark
    assert (not contain_embark)
    
    # Boats are in (47, 27)
    boat_ids = [1549, 1099]
    # 886 in (46, 27), others in (46, 26)
    unit_ids = [886, 1964, 1912, 1868, 1817, 1033, 319, 280, 269]
    action_list = []

    for unit_id in unit_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # if unit_id == 886:
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
        contain_embark = False
        embark_key = ''
        for action_key in valid_actions:
            if 'embark' in action_key:
                contain_embark = True
                embark_key = action_key
                break
        # The unit is besides a boat, the embark action is valid.
        assert (contain_embark)
        if unit_id != 886:
            action_list.append(valid_actions['embark_7_1549'])
    # Show the state of boat 1549.
    print(unit_opt.unit_ctrl.units[1549])

    # Perform embark action for units which is not 886.
    for action in action_list:
        action.trigger_action(controller.ws_client)
    
    print('Embark the boat.')
    controller.send_end_turn()
    controller.get_info()
    controller.get_observation()
    # Show the state of boat 1549 after eight units embark.
    print(unit_opt.unit_ctrl.units[1549])

    for unit_id in unit_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # if unit_id == 886:
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
        contain_embark = False
        embark_key = ''
        for action_key in valid_actions:
            if 'embark' in action_key:
                contain_embark = True
                embark_key = action_key
                break
        if unit_id == 886:
            # The unit is besides a boat, the embark action is valid.
            assert (contain_embark)
            # The boat 1549 is full, cannot boat it.
            assert ('embark_4_1549' not in valid_actions)
            # Perform embark for 886.
            valid_actions['embark_4_1099'].trigger_action(controller.ws_client)
        else:
            # The unit is on boat, the embard action is invalid.
            assert (not contain_embark)

    print('Unit 886 embark the boat.')
    controller.send_end_turn()
    controller.get_info()
    controller.get_observation()
    valid_actions = unit_opt.get_actions(886, valid_only=True)
    print(f'Unit 886, valid action keys: {valid_actions.keys()}')

    

    # import time
    # time.sleep(2)


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T375_2023-08-02-10_04')
    test_embark(controller)


if __name__ == '__main__':
    main()
