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
from freeciv_gym.freeciv.game.ruleset import EXTRA_AIRBASE, EXTRA_FORTRESS
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T370_2023-08-01-06_00')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def test_airbase(controller):
    fc_logger.info("test_airbase")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    unit_id = 843
    punit = unit_opt.unit_ctrl.units[unit_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    print(
        f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}.")
    # Get valid actions
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    assert ('airbase' in valid_actions)
    # Choose airbase action
    valid_actions['airbase'].trigger_action(controller.ws_client)
    controller.get_observation()
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # Already performing airbase. The airbase action is invalid.
    assert ('airbase' not in valid_actions)
    assert (unit_tile['extras'][EXTRA_AIRBASE] == 0)
    print(f'valid action keys: {valid_actions.keys()}')

    # Wait for airbase finish.
    for _ in range(3):
        controller.send_end_turn()
        controller.get_info()
        controller.get_observation()
    print('Airbase built')

    assert (unit_tile['extras'][EXTRA_AIRBASE] == 1)
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # Already has airbase, cannot build again
    assert ('airbase' not in valid_actions)
    print(f'valid action keys: {valid_actions.keys()}')

    # Start to build fortress
    valid_actions['fortress'].trigger_action(controller.ws_client)
    controller.get_observation()
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    assert ('fortress' not in valid_actions)
    assert (unit_tile['extras'][EXTRA_FORTRESS] == 0)
    assert ('airbase' not in valid_actions)
    print(f'valid action keys: {valid_actions.keys()}')

    # Wait for fortress finish.
    for _ in range(3):
        controller.send_end_turn()
        controller.get_info()
        controller.get_observation()
    print('fortress built')

    assert (unit_tile['extras'][EXTRA_AIRBASE] == 1)
    assert (unit_tile['extras'][EXTRA_FORTRESS] == 1)
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # Has both fortress and airbase, cannot build airbase again.
    assert ('airbase' not in valid_actions)
    assert ('fortress' not in valid_actions)
    print(f'valid action keys: {valid_actions.keys()}')

    import time
    time.sleep(2)


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T370_2023-08-01-06_00')
    test_airbase(controller)


if __name__ == '__main__':
    main()