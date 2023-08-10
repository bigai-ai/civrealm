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
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option
import freeciv_gym.freeciv.utils.fc_types as fc_types

@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T376_2023-08-07-07_35')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def test_load_deboard_unload(controller):
    fc_logger.info("test_load_deboard_unload")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']

    for unit_id in unit_opt.unit_data.keys():
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        if (ptile['x'] == 45 and ptile['y'] == 30) or (ptile['x'] == 46 and ptile['y'] == 30):
            print(f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(unit_focus.punit)}, activity: {unit_focus.punit['activity']}.")

        # if unit_id == 1912:
        #     for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        #         if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
        #             print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')
        # print(f'Unit {unit_id}')
        # print(unit_focus.punit)
        # # if unit_id == 1817:
        # #     print(unit_focus.punit)
        # #     print(f"({unit_focus.ptile['x']}, {unit_focus.ptile['y']})")
        # #     print(unit_focus.ptype)
        # valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # print(f'valid actions: {valid_actions.keys()}')
    
    # Boats are in (45, 30) -- a tile with city
    boat_ids = [1549, 1099]
    # Transported units are in (45, 30)
    unit_ids = [886, 1964, 1912]
    action_list = []
    for unit_id in boat_ids+unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # if unit_id == 886:
        # print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
        if unit_id == 1549:
            assert ('unit_unload' in valid_actions)
        if unit_id == 1099:
            # This unit is not in a city, cannot unload its units.
            assert ('unit_unload' not in valid_actions)
            # Move to the city
            valid_actions[f'goto_{map_const.DIR8_WEST}'].trigger_action(controller.ws_client)
        if unit_id in unit_ids:
            # This unit is not transporter, cannot perform unload
            assert ('unit_unload' not in valid_actions)
            # The unit is being transported, cannot perform load
            assert ('board' not in valid_actions)

    # controller.send_end_turn()
    controller.get_info()
    controller.get_observation()

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        print(f"{unit_id} is transported by {unit_focus.punit['transported_by']}")
        # These units is being transported.
        assert (unit_focus.punit['transported'])
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')

        # if unit_id == 1912 or unit_id == 1964:
        #     print(f'Unit: {unit_id}')
        #     for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        #         if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
        #             print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')

    for unit_id in boat_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # Both boats are in a city, can unload.
        assert ('unit_unload' in valid_actions)

        if unit_id == 1549:
            print(f"Boat {unit_id}'s move left before unload: {unit_focus.punit['movesleft']}")
            # Boat 1549 unloads its units.
            valid_actions['unit_unload'].trigger_action(controller.ws_client)
    
    print('Unit 1549 unloads its units.')

    controller.get_info()
    controller.get_observation()
    
    unit_focus = unit_opt.unit_data[1549]
    print(f"Boat {1549}'s move left after unload: {unit_focus.punit['movesleft']}")
    
    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 1912:
            assert (unit_focus.punit['transported'])
        else:
            # Unit 886 and 1964 have been unloaded.
            assert (unit_focus.punit['transported'] == 0)
            assert ('board' in valid_actions)
            valid_actions['board'].trigger_action(controller.ws_client)
            print(f'Unit {unit_id} loading.')
        # print(unit_focus.punit)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')            
        
    controller.get_info()
    controller.get_observation()

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # All units have been onboard.
        assert (unit_focus.punit['transported'] > 0)
        assert ('board' not in valid_actions)
        assert ('deboard' in valid_actions)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
        print(f"{unit_id} is transported by {unit_focus.punit['transported_by']}")
        print(f"Unit {unit_id}\'s activity: {unit_focus.punit['activity']}")
        valid_actions['deboard'].trigger_action(controller.ws_client)

    print('All units deboard.')
    controller.get_info()
    controller.get_observation()

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # All units have deboarded.
        assert (unit_focus.punit['transported'] == 0)
        assert ('board' in valid_actions)
        assert ('deboard' not in valid_actions)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
        print(f"Unit {unit_id}\'s activity: {unit_focus.punit['activity']}")
        print(f"Unit{unit_id}\'s move left: {unit_focus.punit['movesleft']}")

    # import time
    # time.sleep(2)


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T376_2023-08-07-07_35')
    test_load_deboard_unload(controller)


if __name__ == '__main__':
    main()
