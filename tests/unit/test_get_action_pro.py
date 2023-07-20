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
import freeciv_gym.freeciv.map.map_const as map_const


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T82_2023-07-17-03_56')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def test_attack(controller):
    fc_logger.info("test_get_action_pro")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
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
        punit = unit_opt.unit_ctrl.units[unit_id]        
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        # print(
        #     f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
        if unit_id == 396:
            # 396 unit has not move left. It can do nothing.
            assert (len(punit['action_prob']) == 0)
        if unit_id == 250:
            assert(punit['action_prob'][map_const.DIR8_NORTHEAST][fc_types.ACTION_UNIT_MOVE] == {'min': 200, 'max': 200})
            # Attack pros are different given different targets.
            assert(punit['action_prob'][map_const.DIR8_NORTHWEST][fc_types.ACTION_ATTACK] == {'min': 200, 'max': 200})
            assert(punit['action_prob'][map_const.DIR8_SOUTHEAST][fc_types.ACTION_ATTACK] == {'min': 1, 'max': 2})
            # Cannot move to sea (north and west).
            assert(punit['action_prob'][map_const.DIR8_NORTH][fc_types.ACTION_UNIT_MOVE] == {'min': 0, 'max': 0})
            assert(punit['action_prob'][map_const.DIR8_WEST][fc_types.ACTION_UNIT_MOVE] == {'min': 0, 'max': 0})
            # Cannot move to east. TODO: figure out why. Maybe because an enemy unit is doing fortify.
            assert(punit['action_prob'][map_const.DIR8_EAST][fc_types.ACTION_UNIT_MOVE] == {'min': 0, 'max': 0})
            # Can move to own units.
            assert(punit['action_prob'][map_const.DIR8_SOUTH][fc_types.ACTION_UNIT_MOVE])
        if unit_id == 126:
            # Cannot move to enemy unit. Explorer also cannot attack enemy.
            assert(punit['action_prob'][map_const.DIR8_EAST][fc_types.ACTION_UNIT_MOVE] == {'min': 0, 'max': 0})
            assert(punit['action_prob'][map_const.DIR8_EAST][fc_types.ACTION_ATTACK] == {'min': 0, 'max': 0})
        
    # controller.send_end_turn()
    # options = controller.get_info()['available_actions']
    # controller.get_observation()
    # unit_opt = options['unit']
    # for unit_id in unit_opt.unit_data.keys():
    #     punit = unit_opt.unit_ctrl.units[unit_id]        
    #     unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    #     # print(
    #     #     f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
    #     if unit_id == 207:            
    #         print(punit['action_prob'][map_const.DIR8_NORTHEAST][fc_types.ACTION_UNIT_MOVE])
    #         print(punit['action_prob'][map_const.DIR8_NORTHEAST][fc_types.ACTION_ATTACK])