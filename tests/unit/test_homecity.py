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
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T53_2023-07-24-13_02_homecity')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.end_game()
    controller.close()


def test_homecity(controller):
    fc_logger.info("test_homecity")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_id = 158
    unit_opt = options['unit']
    punit = unit_opt.unit_ctrl.units[unit_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    assert ('homecity' in valid_actions.keys())
    unit_action = valid_actions['homecity']
    print(
        f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}, home city: {punit['homecity']}.")
    assert (unit_action.is_action_valid())
    unit_action.trigger_action(controller.ws_client)
    print(f"Change the homecity of unit {unit_id} to the current garissoned city")
    controller.send_end_turn()
    controller.get_observation()
    unit_opt = options['unit']
    punit = unit_opt.unit_ctrl.units[unit_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    print(
        f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_opt.unit_ctrl.get_unit_moves_left(punit)}, home city: {punit['homecity']}.")
    import time
    time.sleep(2)


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T53_2023-07-24-13_02_homecity')
    test_homecity(controller)


if __name__ == '__main__':
    main()
