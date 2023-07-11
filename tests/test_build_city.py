# # Copyright (C) 2023  The Freeciv-gym project
# #
# # This program is free software: you can redistribute it and/or modify it
# # under the terms of the GNU General Public License as published by the Free
# #  Software Foundation, either version 3 of the License, or (at your option)
# # any later version.
# #
# # This program is distributed in the hope that it will be useful, but
# # WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# # or FITNESS FOR A PARsrc/freeciv_gym/configs/default_setting.ymlTICULAR PURPOSE.  See the GNU General Public License for more details.
# #
# # You should have received a copy of the GNU General Public License along
# # with this program.  If not, see <http://www.gnu.org/licenses/>.


import pytest
from freeciv_gym.freeciv.civ_controller import CivController
from freeciv_gym.freeciv.map.map_ctrl import DIR8_SOUTH

@pytest.fixture
def controller():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()

def test_build_city(controller):
    controller.init_network()
    controller.get_observation()
    options= controller.turn_manager.get_available_actions()
    # Class: UnitActions
    unit_opt = options['unit']    
    test_action_list = []
    build_action = None

    for unit_id in unit_opt.unit_ctrl.units.keys():    
        punit = unit_opt.unit_ctrl.units[unit_id]        
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")        
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 137:
            test_action_list.append(valid_actions[f'goto_{DIR8_SOUTH}'])
            build_action = valid_actions['build']
        else:
            pass
    # Perform goto action for each unit
    for action in test_action_list:
        action.trigger_action(controller.ws_client)
    # Get unit new state
    controller.get_observation()
    # The unit has no move left, the build should be invalid
    assert(not build_action.is_action_valid())
    # End turn
    controller.send_end_turn()
    controller.get_observation()
    # The unit has move in new turn, the build should be valid
    assert(build_action.is_action_valid())
    city_num = len(controller.city_ctrl.cities)
    build_action.trigger_action(controller.ws_client)
    # Get unit new state
    controller.get_observation()
    # Building a new city increases the city number
    assert(len(controller.city_ctrl.cities) == city_num+1)