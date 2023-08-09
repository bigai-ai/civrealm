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


def test_trade_route(controller):
    fc_logger.info("test_trade_route")
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
        if unit_id == 1964:
            assert ('trade_route' in valid_actions)
        if unit_id == 1912:
            # This unit is not in a city, cannot establish a trade route.
            assert ('trade_route' not in valid_actions)
        if unit_id == 1099:
            # Move to the city
            valid_actions[f'goto_{map_const.DIR8_WEST}'].trigger_action(controller.ws_client)

    # controller.send_end_turn()
    controller.get_info()
    controller.get_observation()

    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')

        if unit_id == 1912 or unit_id == 1964:
            assert ('trade_route' in valid_actions)
            # print(f'Unit: {unit_id}')
            # for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
            #     if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            #         print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')
        
        if unit_id == 1964:
            # Change the homecity of this unit
            valid_actions['homecity'].trigger_action(controller.ws_client)
   
    controller.get_info()
    controller.get_observation()
    
    for unit_id in unit_ids:
        unit_focus = unit_opt.unit_data[unit_id]
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')

        if unit_id == 1912:
            assert ('trade_route' in valid_actions)
            # print(f'Unit: {unit_id}')
            # for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
            #     if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            #         print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')
            
            valid_actions['trade_route'].trigger_action(controller.ws_client)
            print('Build trade route.')
        
        if unit_id == 1964:
            # This unit has changed the homecity to the current city, cannot build trade route anymore.
            assert ('trade_route' not in valid_actions)
    
    city_id = 414
    # The trade route is empty before 1912 build one.
    assert(city_id not in controller.city_ctrl.city_trade_routes)
    
    controller.get_info()
    controller.get_observation()

    # Unit 1912 has built a trade route.
    
    assert(controller.city_ctrl.city_trade_routes[city_id] != {})

    # import time
    # time.sleep(2)


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T376_2023-08-07-07_35')
    test_trade_route(controller)


if __name__ == '__main__':
    main()
