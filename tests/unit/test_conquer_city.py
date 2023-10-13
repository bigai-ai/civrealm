# Copyright (C) 2023  The CivRealm project
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
from civrealm.freeciv.civ_controller import CivController
import civrealm.freeciv.map.map_const as map_const
import civrealm.freeciv.units.unit_helpers as unit_helpers
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T144_conquer_city')
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
    attacker_id = 161

    punit = unit_opt.unit_ctrl.units[attacker_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    print(
        f"Unit id: {attacker_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}, activity: {punit['activity']}.")
    # Get valid actions
    valid_actions = unit_opt.get_actions(attacker_id, valid_only=True)
    print(valid_actions.keys())

    # The target tile does not belong to our player due to the enemy city.
    target_tile = unit_opt.map_ctrl.mapstep(unit_tile, map_const.DIR8_NORTH)
    assert (not unit_opt.unit_ctrl.city_ctrl.tile_city(target_tile)
            ['owner'] == unit_opt.player_ctrl.my_player_id)
    previous_owner = unit_opt.unit_ctrl.city_ctrl.tile_city(target_tile)['owner']

    print('Conquer the city on the north')
    # Perform conquer city action
    valid_actions[f'conquer_city_{map_const.DIR8_NORTH}'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    assert (punit['tile'] == 1473)
    # The enemy city has been destroyed
    assert (unit_tile['owner'] != previous_owner)


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T144_conquer_city')
    test_conquer_city(controller)


if __name__ == '__main__':
    main()
