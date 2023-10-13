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
from civrealm.freeciv.utils.fc_types import EXTRA_ROAD, EXTRA_RAILROAD
import civrealm.freeciv.map.map_const as map_const
import civrealm.freeciv.units.unit_helpers as unit_helpers
from civrealm.freeciv.utils.freeciv_logging import fc_logger
from civrealm.configs import fc_args
from civrealm.freeciv.utils.test_utils import get_first_observation_option


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T201_2023-07-31-07_46')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_build_railroad(controller):
    fc_logger.info("test_build_railroad")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']

    unit_ids = [109, 236, 259]
    for unit_id in unit_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        build_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)

        if unit_id == 109:
            assert (build_tile['extras'][EXTRA_ROAD] == 1)
            assert (not build_tile['extras'][EXTRA_RAILROAD] == 1)
            # worker on a tile with road, should be able to build railroad
            print(
                f"Unit id: {unit_id}, position: ({build_tile['x']}, {build_tile['y']}), extras[EXTRA_RAILROAD]: {build_tile['extras'][EXTRA_RAILROAD]}, move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
            assert ('build_railroad' in valid_actions)
            print(f'unit_id: {unit_id} build railroad.')
            valid_actions['build_railroad'].trigger_action(controller.ws_client)
        if unit_id == 236:
            # worker on a tile without road, shouldn't be able to build railroad
            assert (not build_tile['extras'][EXTRA_ROAD] == 1)
            assert ('build_railroad' not in valid_actions)
        if unit_id == 259:
            # non-worker unit, shouldn't be able to build railroad
            # cancel fortify orders
            valid_actions['cancel_order'].trigger_action(controller.ws_client)
            controller.get_info_and_observation()
            valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
            # move to northeast tile which has road
            valid_actions[f'goto_{map_const.DIR8_NORTHEAST}'].trigger_action(controller.ws_client)
    controller.get_info_and_observation()
    for unit_id in unit_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        build_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        if unit_id == 259:
            assert (build_tile['extras'][EXTRA_ROAD] == 1)
            assert ('build_railroad' not in valid_actions)

    # wait until railroad is built
    for turn_i in range(3):
        controller.send_end_turn()
        controller.get_info_and_observation()
        # print(unit_opt.unit_ctrl.units[109])
    for unit_id in unit_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        build_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        if unit_id == 109:
            print(
                f"Unit id: {unit_id}, position: ({build_tile['x']}, {build_tile['y']}), extras[EXTRA_RAILROAD]: {build_tile['extras'][EXTRA_RAILROAD]}, move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
            assert (build_tile['extras'][EXTRA_RAILROAD] == 1)


def main():
    controller = CivController('testcontroller')
    controller.set_parameter('debug.load_game', 'testcontroller_T201_2023-07-31-07_46')
    test_build_railroad(controller)


if __name__ == '__main__':
    main()
