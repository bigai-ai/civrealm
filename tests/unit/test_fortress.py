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
from freeciv_gym.freeciv.game.ruleset import EXTRA_FORTRESS
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T133_2023-07-20-15_23_diplcity')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def test_fortress(controller):
    fc_logger.info("test_fortress")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    build_action = None
    worker_id = 535
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    build_action = valid_actions['fortress']
    punit = unit_opt.unit_ctrl.units[worker_id]
    build_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    print(
        f"Unit id: {worker_id}, position: ({build_tile['x']}, {build_tile['y']}), extras[EXTRA_FORTRESS]: {build_tile['extras'][EXTRA_FORTRESS]}, move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
    # The unit has move in new turn, the build should be valid
    assert (not (build_tile['extras'][EXTRA_FORTRESS] == 1))
    assert (build_action.is_action_valid())
    build_action.trigger_action(controller.ws_client)
    print('Begin building a fortress, needs a few turns to finish ...')
    # Wait for 3 turns (until job is done)
    for turn_i in range(3):
        controller.send_end_turn()
        controller.get_observation()
    # Get updated state
    print(
        f"Unit id: {worker_id}, position: ({build_tile['x']}, {build_tile['y']}), extras[EXTRA_FORTRESS]: {build_tile['extras'][EXTRA_FORTRESS]}, move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
    assert (build_tile['extras'][EXTRA_FORTRESS] == 1)
    import time
    time.sleep(2)


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T133_2023-07-20-15_23_diplcity')
    test_fortress(controller)


if __name__ == '__main__':
    main()
