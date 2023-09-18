# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.


import pytest
from freeciv_gym.freeciv.civ_controller import CivController
import freeciv_gym.freeciv.map.map_const as map_const
import freeciv_gym.freeciv.units.unit_helpers as unit_helpers
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.configs import fc_args
from freeciv_gym.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T134_2023-08-17-03_37_sabotage')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_conquer_city(controller):
    fc_logger.info("test_conquer_city")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    musketeer_id = 814

    for unit_id in unit_opt.unit_ctrl.units.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        if unit_id == musketeer_id:
            print(
                f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
            # Get valid actions
            valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
            test_action_list.append(valid_actions[f'conquer_city_{map_const.DIR8_SOUTHWEST}'])
            target_tile = unit_opt.map_ctrl.mapstep(unit_tile, map_const.DIR8_SOUTHWEST)
            assert (not unit_opt.unit_ctrl.city_ctrl.tile_city(target_tile)
                    ['owner'] == unit_opt.player_ctrl.my_player_id)
            break
        else:
            pass
    print('Conquer the city on southwest tile')
    # Perform conquer city action
    for action in test_action_list:
        action.trigger_action(controller.ws_client)
    # Get unit new state
    controller.send_end_turn()
    controller.get_info_and_observation()
    options = controller.turn_manager.turn_actions
    unit_opt = options['unit']
    punit = unit_opt.unit_ctrl.units[musketeer_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    # The enemy city is now under our rule
    assert (unit_opt.unit_ctrl.city_ctrl.tile_city(unit_tile)['owner'] == unit_opt.player_ctrl.my_player_id)

def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T134_2023-08-17-03_37_sabotage')
    test_conquer_city(controller)


if __name__ == '__main__':
    main()
