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


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T375_embark_disembark')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_embark_disembark(controller):
    fc_logger.info("test_embark")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']

    for unit_id in unit_opt.unit_data.keys():
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        if ptile['x'] == 47 and ptile['y'] == 28:
            print(
                f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, unit_focus.punit)}.")

    # Plane is in (47, 28)
    plane_id = 1841

    valid_actions = unit_opt.get_actions(plane_id, valid_only=True)
    print(f'Unit {plane_id}, valid action keys: {valid_actions.keys()}')
    contain_embark = False
    for action_key in valid_actions:
        if action_key.startswith('embark'):
            contain_embark = True
            break
    # The unit is a plane, cannot embark
    assert (not contain_embark)

    # Boats are in (47, 27)
    boat_ids = [1549, 1099]
    # 886 in (46, 27), others in (46, 26)
    unit_ids = [886, 1964, 1912, 1868, 1817, 1033, 319, 280, 269]
    action_list = []

    for unit_id in unit_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # if unit_id == 886:
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
        contain_embark = False
        embark_key = ''
        for action_key in valid_actions:
            if action_key.startswith('embark'):
                contain_embark = True
                embark_key = action_key
                break
        # The unit is besides a boat, the embark action is valid.
        assert (contain_embark)
        if unit_id != 886:
            action_list.append(valid_actions['embark_7_1549'])
        if unit_id == 886:
            action_list.append(valid_actions['pillage'])
    # Show the state of boat 1549.
    print(unit_opt.unit_ctrl.units[1549])

    # Perform embark action for units which is not 886.
    for action in action_list:
        action.trigger_action(controller.ws_client)

    print('Embark the boat.')
    # controller.send_end_turn()
    controller.get_info_and_observation()
    # Show the state of boat 1549 after eight units embark.
    print(unit_opt.unit_ctrl.units[1549])

    unit_id = 886
    punit = unit_opt.unit_ctrl.units[unit_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    print(
        f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    # Get valid actions
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')
    contain_embark = False
    for action_key in valid_actions:
        if action_key.startswith('embark'):
            contain_embark = True
            break
    # The unit is currently under pillage activity, but we cancel the activity before query the pro, so the returned embark pro is not 0.
    assert (contain_embark)
    # Cancel the pillage order
    valid_actions['cancel_order'].trigger_action(controller.ws_client)
    print('Cancel unit 886 order.')
    controller.send_end_turn()
    controller.get_info_and_observation()

    for unit_id in unit_ids:
        punit = unit_opt.unit_ctrl.units[unit_id]
        unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
        print(
            f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
        # Get valid actions
        valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        # if unit_id == 886:
        print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')

        # unit_focus = unit_opt.unit_data[unit_id]
        # for i in range(len(unit_focus.action_prob[map_const.DIR8_WEST])):
        #     if unit_focus.action_prob[map_const.DIR8_WEST][i] != {'min': 0, 'max': 0}:
        #         print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_WEST][i]}')

        contain_embark = False
        embark_key = ''
        for action_key in valid_actions:
            if action_key.startswith('embark'):
                contain_embark = True
                embark_key = action_key
                break
        if unit_id == 886:
            # The unit is besides a boat, the embark action is valid.
            assert (contain_embark)
            # The boat 1549 is full, cannot boat it.
            assert ('embark_4_1549' not in valid_actions)
            # Perform embark for 886.
            valid_actions['embark_4_1099'].trigger_action(controller.ws_client)
        else:
            # The unit is on boat, the embark action is invalid.
            assert (not contain_embark)

    print('Unit 886 embark the boat.')
    controller.send_end_turn()
    controller.get_info_and_observation()
    valid_actions = unit_opt.get_actions(886, valid_only=True)
    print(f'Unit 886, valid action keys: {valid_actions.keys()}')
    print(
        f"Unit {886}'s move left before disembark: {unit_opt.unit_data[886].punit['movesleft']}, activity: {unit_opt.unit_data[886].punit['activity']}")

    # Disembark to the north
    valid_actions['disembark_1'].trigger_action(controller.ws_client)

    valid_actions = unit_opt.get_actions(319, valid_only=True)
    print(f'Unit 319, valid action keys: {valid_actions.keys()}')

    controller.send_end_turn()
    controller.get_info_and_observation()

    unit_id = 886
    punit = unit_opt.unit_ctrl.units[unit_id]
    unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    print(
        f"Unit id: {unit_id}, position: ({unit_tile['x']}, {unit_tile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, punit)}.")
    assert (unit_tile['x'] == 47 and unit_tile['y'] == 26)
    # Get valid actions
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    # if unit_id == 886:
    print(f'Unit {unit_id}, valid action keys: {valid_actions.keys()}')

    # unit_focus = unit_opt.unit_data[319]
    # for i in range(len(unit_focus.action_prob[map_const.DIR8_WEST])):
    #     if unit_focus.action_prob[map_const.DIR8_WEST][i] != {'min': 0, 'max': 0}:
    #         print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_WEST][i]}')

    # for i in range(len(unit_focus.action_prob[map_const.DIR8_SOUTHWEST])):
    #     if unit_focus.action_prob[map_const.DIR8_SOUTHWEST][i] != {'min': 0, 'max': 0}:
    #         print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_SOUTHWEST][i]}')

    # for i in range(len(unit_focus.action_prob[map_const.DIR8_NORTH])):
    #     if unit_focus.action_prob[map_const.DIR8_NORTH][i] != {'min': 0, 'max': 0}:
    #         print(f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_NORTH][i]}')


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T375_embark_disembark')
    test_embark_disembark(controller)


if __name__ == '__main__':
    main()
