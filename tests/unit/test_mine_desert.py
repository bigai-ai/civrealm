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
from freeciv_gym.freeciv.utils.fc_types import EXTRA_OIL_MINE
import freeciv_gym.freeciv.map.map_const as map_const
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T139_2023-07-28-09_49')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_mine_desert(controller):
    fc_logger.info("test_mine_desert")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    build_action = None
    worker_id = 1006
    unit_focus = unit_opt.unit_data[worker_id]
    ptile = unit_focus.ptile
    # There is no oil mine extra
    assert (ptile['extras'][EXTRA_OIL_MINE] == 0)
    print(
        f"Unit id: {worker_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(unit_focus.punit)}.")

    # Get valid actions
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    assert ('mine' in valid_actions)
    # Trigger mine action
    valid_actions[f'mine'].trigger_action(controller.ws_client)
    # Wait for 5 turns (until the work is done)
    for turn_i in range(5):
        controller.send_end_turn()
        controller.get_info()
        controller.get_observation()
    # Build oil mine extra
    assert (ptile['extras'][EXTRA_OIL_MINE] == 1)

    # Get valid actions again
    valid_actions = unit_opt.get_actions(worker_id, valid_only=True)
    # Cannot mine again
    assert ('mine' not in valid_actions)

    import time
    time.sleep(2)


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T139_2023-07-28-09_49')
    test_mine_desert(controller)


if __name__ == '__main__':
    main()
