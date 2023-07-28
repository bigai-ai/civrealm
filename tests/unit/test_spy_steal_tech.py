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


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T133_2023-07-27-08_36')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def test_spy_steal_tech(controller):
    fc_logger.info("test_spy_steal_tech")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    player_opt = options['player']
    test_action_list = []
    diplomat_id = 915
    
    for unit_id in unit_opt.unit_ctrl.units.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        if unit_id == diplomat_id:
            print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
            # Get valid actions
            valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
            test_action_list.append(valid_actions[f'spy_steal_tech_{map_const.DIR8_SOUTH}'])
            break
        else:
            pass
    print('Steal technology from the city on the southwest tile')
    techs_researched_before = player_opt.players[0]['techs_researched']
    assert (True)
    # Perform spy_bribe_unit action for the diplomat
    for action in test_action_list:
        action.trigger_action(controller.ws_client)
    # Get unit new state
    controller.send_end_turn()
    options = controller.get_info()['available_actions']
    controller.get_observation()
    unit_opt = options['unit']
    player_opt = options['player']
    techs_researched_after = player_opt.players[0]['techs_researched']
    assert (techs_researched_after == techs_researched_before + 1)
    import time
    time.sleep(2)
    
def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T133_2023-07-27-08_36')
    test_spy_steal_tech(controller)


if __name__ == '__main__':
    main()