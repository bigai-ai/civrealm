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
import civrealm.freeciv.utils.fc_types as fc_types
from civrealm.freeciv.utils.fc_types import EXTRA_HUT, ACTIVITY_GEN_ROAD


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T28_hut_enter')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_hut_enter(controller):
    fc_logger.info("test_hut_enter")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']
    # print(unit_opt.unit_ctrl.units.keys())
    test_action_list = []
    target_tile = None
    for unit_id in unit_opt.unit_data.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        # print(
        #     f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        unit_focus = unit_opt.unit_data[unit_id]
        if unit_id == 156:
            # Not hut in the north
            assert ('hut_enter_1' not in valid_actions)
            # Go to north
            test_action_list.append(valid_actions[f'goto_{map_const.DIR8_NORTH}'])

        elif unit_id == 138:
            assert ('hut_enter_2' in valid_actions)
            # This unit is building road.
            assert (punit['activity'] == ACTIVITY_GEN_ROAD)
            test_action_list.append(valid_actions['hut_enter_2'])
            target_tile = unit_opt.map_ctrl.mapstep(unit_tile, map_const.DIR8_NORTHEAST)
            assert (target_tile['extras'][EXTRA_HUT] == 1)

    # Perform goto action for each unit
    for action in test_action_list:
        action.trigger_action(controller.ws_client)

    # Update state. If Hut Enter action does not cancel activity, the hut_enter action would not take effect. Then the client will keep wait for packet 63.
    controller.get_info_and_observation()
    # After enter hut, the extra disappears.
    assert (target_tile['extras'][EXTRA_HUT] == 0)

    # End turn to give new move for unit 156
    controller.send_end_turn()
    controller.get_info_and_observation()
    for unit_id in unit_opt.unit_ctrl.units.keys():
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])

        if unit_id == 156:
            valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
            # There is a hut in the north.
            assert ('hut_enter_1' in valid_actions)
            # Enter hut
            valid_actions['hut_enter_1'].trigger_action(controller.ws_client)
            target_tile = unit_opt.map_ctrl.mapstep(unit_tile, map_const.DIR8_NORTH)
            assert (target_tile['extras'][EXTRA_HUT] == 1)

    controller.get_info_and_observation()
    # After enter hut, the extra disappears.
    assert (target_tile['extras'][EXTRA_HUT] == 0)


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T28_hut_enter')
    test_hut_enter(controller)


if __name__ == '__main__':
    main()
