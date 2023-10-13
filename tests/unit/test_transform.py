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
    controller.set_parameter('debug.load_game', 'testcontroller_T391_transform')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_transform(controller):
    fc_logger.info("test_transform")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    worker_ids = [931, 920, 818]
    boat_id = 1603
    for unit_id in worker_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        terrain = unit_opt.rule_ctrl.tile_terrain(unit_tile)
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # print(f'Valid actions: {valid_actions.keys()}')
        if unit_id == 931 or unit_id == 818:
            # 931 is on swamp while none of the neighboring tiles is ocean. So transform is impossible.
            assert ('transform_terrain' not in valid_actions)
        else:
            assert ('transform_terrain' in valid_actions)
            # Perform transform
            valid_actions['transform_terrain'].trigger_action(controller.ws_client)

    boat_valid_actions = unit_opt.get_actions(boat_id, valid_only=True)
    # Boat goes to west
    print('Boat moves.')
    boat_valid_actions[f'goto_{map_const.DIR8_WEST}'].trigger_action(controller.ws_client)

    old_terrain_name = ''
    # Get unit new state
    controller.get_info_and_observation()
    for unit_id in worker_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        terrain = unit_opt.rule_ctrl.tile_terrain(unit_tile)
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # Here the server has a bug: when the boat moves, the transported engineer should be able to do transform. However, the returned action probability is still 0.
        assert ('transform_terrain' not in valid_actions)
        # print(f'Valid actions: {valid_actions.keys()}')
        if unit_id == 920:
            old_terrain_name = terrain['name']
            # print(terrain)

    print(f'Unit {920} is on a terrain: {old_terrain_name}')
    print('Start to transform...')
    # End turn for transform activity.
    for _ in range(18):
        controller.send_end_turn()
        controller.get_info_and_observation()

    punit = unit_opt.unit_ctrl.units[920]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    terrain = unit_opt.rule_ctrl.tile_terrain(unit_tile)
    new_terrain_name = terrain['name']
    print(f'Unit {920} now is on a terrain: {new_terrain_name}')

    assert (old_terrain_name != new_terrain_name)


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T391_transform')
    test_transform(controller)


if __name__ == '__main__':
    main()
