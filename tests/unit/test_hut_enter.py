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
from freeciv_gym.freeciv.game.ruleset import EXTRA_HUT

@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def test_hut_enter(controller):
    fc_logger.info("test_hut_enter")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    # print(unit_opt.unit_ctrl.units.keys())
    test_action_list = []
    target_tile = None
    for unit_id in unit_opt.unit_ctrl.units.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        # print(
        #     f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        unit_focus = unit_opt.unit_data[unit_id]
        if unit_id == 156:
            # Not hut in the north
            assert ('hut_enter_1' not in valid_actions)
            # Go to north
            test_action_list.append(valid_actions[f'goto_{map_const.DIR8_NORTH}'])

        elif unit_id == 138:
            assert ('hut_enter_2' in valid_actions)
            test_action_list.append(valid_actions['hut_enter_2'])
            target_tile = unit_opt.map_ctrl.mapstep(unit_tile, map_const.DIR8_NORTHEAST)
            assert (target_tile['extras'][EXTRA_HUT] == 1)
    # Perform goto action for each unit
    for action in test_action_list:
        action.trigger_action(controller.ws_client)
    # Get unit new state
    # options = controller.get_info()['available_actions']
    controller.send_end_turn()
    controller.get_info()
    controller.get_observation()
    # After enter hut, the extra disappears.
    assert (target_tile['extras'][EXTRA_HUT] == 0)
    for unit_id in unit_opt.unit_ctrl.units.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        
        if unit_id == 156:
            valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
            # There is a hut in the north.
            assert ('hut_enter_1' in valid_actions)
            # Enter hut
            valid_actions['hut_enter_1'].trigger_action(controller.ws_client)
            target_tile = unit_opt.map_ctrl.mapstep(unit_tile, map_const.DIR8_NORTH)
            assert (target_tile['extras'][EXTRA_HUT] == 1)
    
    controller.get_info()
    controller.get_observation()
    # After enter hut, the extra disappears.
    assert (target_tile['extras'][EXTRA_HUT] == 0)

def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    test_hut_enter(controller)


if __name__ == '__main__':
    main()
