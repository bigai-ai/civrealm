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
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_cultivate(controller):
    fc_logger.info("test_cultivate")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    test_action_list = []
    worker_ids = [137, 138, 139]
    for unit_id in worker_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        terrain = unit_opt.rule_ctrl.tile_terrain(unit_tile)
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        # print(terrain)
        assert (terrain['cultivate_time'] == 0)
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 137:
            assert ('cultivate' not in valid_actions)
            test_action_list.append(valid_actions[f'goto_{map_const.DIR8_EAST}'])
        elif unit_id == 139:
            assert ('cultivate' not in valid_actions)
            test_action_list.append(valid_actions[f'goto_{map_const.DIR8_WEST}'])
    # Perform goto action for the worker
    for action in test_action_list:
        action.trigger_action(controller.ws_client)

    # Get unit new state
    controller.send_end_turn()
    # # Tile info won't update unless options get assigned here
    controller.get_info_and_observation()
    for unit_id in worker_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        terrain = unit_opt.rule_ctrl.tile_terrain(unit_tile)
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        if unit_id == 139:
            # Forest's cultivate is larger than 0.
            assert (terrain['cultivate_time'] > 0)
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 137 or unit_id == 138:
            # Plant forest
            valid_actions[f'plant'].trigger_action(controller.ws_client)
        if unit_id == 139:
            assert ('cultivate' in valid_actions)

    # Wait for 15 turns to finish plant
    for _ in range(15):
        controller.send_end_turn()
        controller.get_info_and_observation()

    for unit_id in worker_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        terrain = unit_opt.rule_ctrl.tile_terrain(unit_tile)
        assert (terrain['cultivate_time'] > 0)
        assert (terrain['name'] == 'Forest')
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        assert ('cultivate' in valid_actions)
        # Perform cultivate action
        valid_actions[f'cultivate'].trigger_action(controller.ws_client)

    # Wait for 5 turns to finish cultivate.
    for _ in range(5):
        controller.send_end_turn()
        controller.get_info_and_observation()

    for unit_id in worker_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        terrain = unit_opt.rule_ctrl.tile_terrain(unit_tile)
        # Forest has been removed.
        assert (terrain['name'] != 'Forest')
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        assert ('cultivate' not in valid_actions)
        # The terrain which had forest before should allow plant action.
        assert ('plant' in valid_actions)


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    test_cultivate(controller)


if __name__ == '__main__':
    main()
