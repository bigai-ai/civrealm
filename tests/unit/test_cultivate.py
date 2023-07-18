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


def test_cultivate(controller):
    fc_logger.info("test_build_city")
    get_first_observation(controller)
    options = controller.turn_manager.get_available_actions()
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    worker_id = 139
    for unit_id in unit_opt.unit_ctrl.units.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == worker_id:
            test_action_list.append(valid_actions[f'goto_{map_const.DIR8_WEST}'])
        else:
            pass
    print('Move to the west tile which has forest')
    # Perform goto action for the worker
    for action in test_action_list:
        action.trigger_action(controller.ws_client)
    # Get unit new state
    controller.send_end_turn()
    controller.get_observation()

    # Tile info won't update unless options get assigned here
    options = controller.turn_manager.get_available_actions()
    unit_opt = options['unit']
    punit = unit_opt.unit_ctrl.units[worker_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    cultivate_action = valid_actions['cultivate']
    print(
        f"Unit id: {worker_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
    assert (cultivate_action.is_action_valid())
    assert (unit_opt.rule_ctrl.tile_terrain(unit_tile)['name'] == 'Forest')
    cultivate_action.trigger_action(controller.ws_client)
    print('Begin cultivating, needs a few turns to finish ...')
    # Wait for 15 turns (until the work is done)
    for turn_i in range(15):
        controller.send_end_turn()
        controller.get_observation()
    assert (unit_opt.rule_ctrl.tile_terrain(unit_tile)['name'] != 'Forest')


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    test_cultivate(controller)


if __name__ == '__main__':
    main()
