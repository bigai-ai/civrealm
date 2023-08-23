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
from freeciv_gym.freeciv.utils.fc_types import EXTRA_ROAD
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T54_2023-07-19-11_58')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_pillage(controller):
    fc_logger.info("test_pillage")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    worker_id = 138
    for unit_id in unit_opt.unit_ctrl.units.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == worker_id:
            test_action_list.append(valid_actions[f'goto_{map_const.DIR8_EAST}'])
        else:
            pass
    print('Move to the east tile which has road & irrigation')
    # Perform goto action for the worker
    for action in test_action_list:
        action.trigger_action(controller.ws_client)
    # Get unit new state
    controller.send_end_turn()
    # Tile info won't update unless options get assigned here
    options = controller.get_info()['available_actions']
    controller.get_observation()

    unit_opt = options['unit']
    punit = unit_opt.unit_ctrl.units[worker_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    unit_action = valid_actions['pillage']
    print(
        f"Unit id: {worker_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
    assert (unit_action.is_action_valid())
    assert (unit_tile['extras'][EXTRA_ROAD] == 1)
    unit_action.trigger_action(controller.ws_client)
    print('Begin pillaging, needs a few turns to finish ...')
    # Wait for 15 turns (until the work is done)
    for turn_i in range(3):
        controller.send_end_turn()
        controller.get_observation()
    assert (not (unit_tile['extras'][EXTRA_ROAD] == 1))
    import time
    time.sleep(2)


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T54_2023-07-19-11_58')
    test_pillage(controller)


if __name__ == '__main__':
    main()
