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


def test_load_unload(controller):
    fc_logger.info("test_load_unload")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']

    for unit_id in unit_opt.unit_data.keys():
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        if ptile['x'] == 45 and ptile['y'] == 30:
            print(f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(unit_focus.punit)}.")
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
            assert ('unload' in valid_actions)
        if unit_id == 1099:
            # This unit is not in a city, cannot unload its units.
            assert ('unload' not in valid_actions)
            # Move to the city
            valid_actions[f'goto_{map_const.DIR8_WEST}'].trigger_action(controller.ws_client)
        if unit_id in unit_ids:
            # This unit is not transporter, cannot perform unload
            assert ('unload' not in valid_actions)

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

    for unit_id in boat_ids:
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # Both boats are in a city, can unload.
        assert ('unload' in valid_actions)

        if unit_id == 1549:
            # Boat 1549 unloads its units.
            valid_actions['unload'].trigger_action(controller.ws_client)
        
    controller.get_info()
    controller.get_observation()

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        if unit_id == 1912:
            assert (unit_focus.punit['transported'])
        else:
            # Unit 886 and 1964 have been unloaded.
            assert (unit_focus.punit['transported'] == 0)
        # print(unit_focus.punit)
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')            
        

    # for id in boat_ids:
    #     print(f'Unit: {id}')
    #     unit_focus = unit_opt.unit_data[id]
    #     for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
    #         if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
    #             print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_WEST][i]}')

    #     for i in range(len(unit_focus.action_prob[map_const.DIR8_NORTH])):
    #         if unit_focus.action_prob[map_const.DIR8_NORTH][i] != {'min': 0, 'max': 0}:
    #             print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_NORTH][i]}')
    #     print('=========================')

    # for id in unit_ids:
    #     print(f'Unit: {id}')
    #     unit_focus = unit_opt.unit_data[id]
    #     for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
    #         if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
    #             print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_WEST][i]}')

    #     for i in range(len(unit_focus.action_prob[map_const.DIR8_NORTH])):
    #         if unit_focus.action_prob[map_const.DIR8_NORTH][i] != {'min': 0, 'max': 0}:
    #             print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_NORTH][i]}')
        
    #     print('=========================')

    # for unit_id in unit_ids:
    #     punit = unit_opt.unit_ctrl.units[unit_id]
    #     unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    #     print(
    #         f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
    #     # Get valid actions
    #     valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    #     # if unit_id == 886:
    #     print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
    #     contain_embark = False
    #     embark_key = ''
    #     for action_key in valid_actions:
    #         if action_key.startswith('embark'):
    #             contain_embark = True
    #             embark_key = action_key
    #             break
    #     # The unit is besides a boat, the embark action is valid.
    #     assert (contain_embark)
    #     if unit_id != 886:
    #         action_list.append(valid_actions['embark_7_1549'])
    #     if unit_id == 886:
    #         action_list.append(valid_actions['pillage'])
    # # Show the state of boat 1549.
    # print(unit_opt.unit_ctrl.units[1549])

    # # Perform embark action for units which is not 886.
    # for action in action_list:
    #     action.trigger_action(controller.ws_client)
    
    # print('Embark the boat.')
    # # controller.send_end_turn()
    # controller.get_info()
    # controller.get_observation()
    # # Show the state of boat 1549 after eight units embark.
    # print(unit_opt.unit_ctrl.units[1549])

    # unit_id = 886
    # punit = unit_opt.unit_ctrl.units[unit_id]
    # unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    # print(
    #     f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
    # # Get valid actions
    # valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
    # contain_embark = False
    # for action_key in valid_actions:
    #     if action_key.startswith('embark'):
    #         contain_embark = True
    #         break
    # # The unit is currently under pillage activity, but we cancel the activity before query the pro, so the returned embark pro is not 0.
    # assert (contain_embark)
    # # Cancel the pillage order
    # valid_actions['cancel_order'].trigger_action(controller.ws_client)
    # print('Cancel unit 886 order.')
    # controller.send_end_turn()
    # controller.get_info()
    # controller.get_observation()

    # for unit_id in unit_ids:
    #     punit = unit_opt.unit_ctrl.units[unit_id]
    #     unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    #     print(
    #         f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
    #     # Get valid actions
    #     valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    #     # if unit_id == 886:
    #     print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')

    #     # unit_focus = unit_opt.unit_data[unit_id]
    #     # for i in range(len(unit_focus.action_prob[map_const.DIR8_WEST])):
    #     #     if unit_focus.action_prob[map_const.DIR8_WEST][i] != {'min': 0, 'max': 0}:
    #     #         print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_WEST][i]}')

    #     contain_embark = False
    #     embark_key = ''
    #     for action_key in valid_actions:
    #         if action_key.startswith('embark'):
    #             contain_embark = True
    #             embark_key = action_key
    #             break
    #     if unit_id == 886:
    #         # The unit is besides a boat, the embark action is valid.
    #         assert (contain_embark)
    #         # The boat 1549 is full, cannot boat it.
    #         assert ('embark_4_1549' not in valid_actions)
    #         # Perform embark for 886.
    #         valid_actions['embark_4_1099'].trigger_action(controller.ws_client)
    #     else:
    #         # The unit is on boat, the embark action is invalid.
    #         assert (not contain_embark)

    # print('Unit 886 embark the boat.')
    # controller.send_end_turn()
    # controller.get_info()
    # controller.get_observation()
    # valid_actions = unit_opt.get_actions(886, valid_only=True)
    # print(f'Unit 886, valid action keys: {valid_actions.keys()}')
    # # Disembark to the north
    # valid_actions['disembark_1'].trigger_action(controller.ws_client)

    # valid_actions = unit_opt.get_actions(319, valid_only=True)
    # print(f'Unit 319, valid action keys: {valid_actions.keys()}')

    # controller.send_end_turn()
    # controller.get_info()
    # controller.get_observation()

    # unit_id = 886
    # punit = unit_opt.unit_ctrl.units[unit_id]
    # unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    # print(
    #     f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
    # assert(unit_tile['x'] == 47 and unit_tile['y'] == 26)
    # # Get valid actions
    # valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # # if unit_id == 886:
    # print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
    
    # unit_focus = unit_opt.unit_data[319]
    # for i in range(len(unit_focus.action_prob[map_const.DIR8_WEST])):
    #     if unit_focus.action_prob[map_const.DIR8_WEST][i] != {'min': 0, 'max': 0}:
    #         print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_WEST][i]}')

    # for i in range(len(unit_focus.action_prob[map_const.DIR8_SOUTHWEST])):
    #     if unit_focus.action_prob[map_const.DIR8_SOUTHWEST][i] != {'min': 0, 'max': 0}:
    #         print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_SOUTHWEST][i]}')

    # for i in range(len(unit_focus.action_prob[map_const.DIR8_NORTH])):
    #     if unit_focus.action_prob[map_const.DIR8_NORTH][i] != {'min': 0, 'max': 0}:
    #         print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_NORTH][i]}')

    # import time
    # time.sleep(2)


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T376_2023-08-07-07_35')
    test_load_unload(controller)


if __name__ == '__main__':
    main()