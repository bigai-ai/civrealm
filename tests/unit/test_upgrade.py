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
import freeciv_gym.freeciv.units.unit_helpers as unit_helpers
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option
from freeciv_gym.freeciv.utils.fc_types import ACTIVITY_FORTIFIED


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T133_2023-07-25-08_57')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_upgrade(controller):
    fc_logger.info("test_upgrade")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_id = 739
    unit_opt = options['unit']
    punit = unit_opt.unit_ctrl.units[unit_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    assert (punit['type'] == 6 and 'upgrade' in valid_actions.keys())
    unit_action = valid_actions['upgrade']
    print(
        f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    assert (unit_action.is_action_valid())
    unit_action.trigger_action(controller.ws_client)
    print(f"Upgrade unit {unit_id} from Legion to Musketeers")
    controller.send_end_turn()
    options = controller.get_info()['available_actions']
    controller.get_observation()
    unit_opt = options['unit']
    punit = unit_opt.unit_ctrl.units[unit_id]
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    assert (punit['type'] == 8 and not ('upgrade' in valid_actions.keys()))
    import time
    time.sleep(2)


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T133_2023-07-25-08_57')
    test_upgrade(controller)


if __name__ == '__main__':
    main()
