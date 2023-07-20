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
from freeciv_gym.freeciv.utils.test_utils import get_first_observation


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def test_attack(controller):
    fc_logger.info("test_attack")
    get_first_observation(controller)
    options = controller.turn_manager.get_available_actions()
    # Class: UnitActions
    unit_opt = options['unit']
    # print(unit_opt.unit_ctrl.units.keys())
    test_action_list = []
    origin_position = {}
    # Get all units (including those controlled by other players)
    # for unit_id in unit_opt.unit_ctrl.units.keys():
    # Get all unit type information
    # for type in unit_opt.rule_ctrl.unit_types:
    #     name = unit_opt.rule_ctrl.unit_types[type]['name']
    #     if name == 'Nuclear' or name == 'Helicopter' or name == 'Horsemen':
    #         print(unit_opt.rule_ctrl.unit_types[type])
    #         print('===============')
    # Get all units controlled by the current player
    for unit_id in unit_opt.unit_data.keys():
        punit = unit_opt.unit_data[unit_id].punit        
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        # print(
        #     f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")        
        if punit['id'] == 250:        
            # adjacent_tiles = unit_opt.map_ctrl.get_adjacent_tiles(unit_tile)
            # for tile in adjacent_tiles:                
            #     print(f"({tile['x']}, {tile['y']}), Units: {tile['units']}")
            #     print('=============')
            adjacent_units = unit_opt.get_adjacent_enemy_units(unit_tile)
            print(adjacent_units)
            # for unit in adjacent_units:                
            #     print(adjacent_units[unit])
            #     print('=============')



        # Get valid actions
        # valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        
    # Perform goto action for each unit
    for action in test_action_list:
        action.trigger_action(controller.ws_client)
    # Get unit new state
    controller.get_observation()
    options = controller.turn_manager.get_available_actions()
    unit_opt = options['unit']
   
        
def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T82_2023-07-17-03_56')
    test_attack(controller)


if __name__ == '__main__':
    main()
