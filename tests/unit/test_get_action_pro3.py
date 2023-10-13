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
import civrealm.freeciv.map.map_const as map_const
from civrealm.freeciv.utils.utility import byte_to_bit_array, find_set_bits
from BitVector import BitVector
from civrealm.freeciv.utils.fc_types import EXTRA_ROAD, EXTRA_MINE


@pytest.fixture
def controller():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    yield controller
    # Delete gamesave saved in handle_begin_turn
    controller.handle_end_turn(None)
    controller.close()


def test_get_action_pro3(controller):
    fc_logger.info("test_get_action_pro3")
    _, options = get_first_observation_option(controller)
    # Class: UnitActions
    unit_opt = options['unit']

    # Get all units (including those controlled by other players)
    # for unit_id in unit_opt.unit_ctrl.units.keys():
    # Get all unit type information
    # for type in unit_opt.rule_ctrl.unit_types:
    #     name = unit_opt.rule_ctrl.unit_types[type]['name']
    #     if name == 'Nuclear' or name == 'Helicopter' or name == 'Horsemen':
    #         print(unit_opt.rule_ctrl.unit_types[type])
    #         print('===============')
    # Get all units controlled by the current player

    for unit_id in unit_opt.unit_data.keys():
        unit_focus = unit_opt.unit_data[unit_id]
        ptile = unit_focus.ptile
        # print(
        #     f"Unit id: {unit_id}, position: ({ptile['x']}, {ptile['y']}), move left: {unit_helpers.get_unit_moves_left(unit_opt.rule_ctrl, unit_focus.punit)}.")
        if unit_id == 138:
            punit = unit_opt.unit_ctrl.units[unit_id]
            unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
            for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
                if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
                    print(
                        f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')
            valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
            valid_actions['plant'].trigger_action(controller.ws_client)
        # if unit_id == 137:
        #     valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
        #     valid_actions[f'goto_{map_const.DIR8_WEST}'].trigger_action(controller.ws_client)

    for turn_i in range(10):
        controller.send_end_turn()
        controller.get_info_and_observation()
    print('Plant')

    unit_focus = unit_opt.unit_data[138]
    ptile = unit_focus.ptile
    print(f"({ptile['x']}, {ptile['y']})")
    # print(unit_focus.punit)
    assert (unit_opt.rule_ctrl.tile_terrain(unit_tile)['name'] == 'Forest')
    for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            print(
                f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')
    valid_actions = unit_opt.get_actions(138, valid_only=True)
    valid_actions[f'goto_{map_const.DIR8_SOUTH}'].trigger_action(controller.ws_client)
    controller.send_end_turn()
    controller.get_info_and_observation()
    print("Move south")

    ptile = unit_focus.ptile
    print(f"({ptile['x']}, {ptile['y']})")
    for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            print(
                f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')
    valid_actions = unit_opt.get_actions(138, valid_only=True)
    assert ('mine' in valid_actions)
    # TODO: current server does not return correct probability for build_road action in the hill. If this assert fails in the future, we can update the action_valid() for build_road action.
    assert (unit_focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_ROAD] == {'min': 0, 'max': 0})
    valid_actions['mine'].trigger_action(controller.ws_client)
    for turn_i in range(11):
        controller.send_end_turn()
        controller.get_info_and_observation()
    print('Mine')

    for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            print(
                f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')
    assert (unit_focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_PILLAGE] == {'min': 200, 'max': 200})
    build_tile = unit_opt.map_ctrl.index_to_tile(unit_focus.punit['tile'])
    print(f"extras[EXTRA_MINE]: {build_tile['extras'][EXTRA_MINE]}")
    print(f"Extra set bit: {find_set_bits(build_tile['extras'])}")
    valid_actions = unit_opt.get_actions(138, valid_only=True)
    valid_actions['pillage'].trigger_action(controller.ws_client)
    for turn_i in range(1):
        controller.send_end_turn()
        controller.get_info_and_observation()
    print('Pillage')

    for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            print(
                f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')
    print(f"Extra set bit: {find_set_bits(build_tile['extras'])}")

    valid_actions = unit_opt.get_actions(138, valid_only=True)
    valid_actions[f'goto_{map_const.DIR8_SOUTH}'].trigger_action(controller.ws_client)
    controller.send_end_turn()
    controller.get_info_and_observation()
    print("Move south")

    ptile = unit_focus.ptile
    print(f"({ptile['x']}, {ptile['y']})")
    for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            print(
                f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')

    valid_actions = unit_opt.get_actions(138, valid_only=True)
    valid_actions['mine'].trigger_action(controller.ws_client)
    for turn_i in range(10):
        controller.send_end_turn()
        controller.get_info_and_observation()
    print('Mine')

    build_tile = unit_opt.map_ctrl.index_to_tile(unit_focus.punit['tile'])
    print(f"extras[EXTRA_MINE]: {build_tile['extras'][EXTRA_MINE]}")
    print(f"extras[EXTRA_ROAD]: {build_tile['extras'][EXTRA_ROAD]}")
    for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            print(
                f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')

    valid_actions = unit_opt.get_actions(138, valid_only=True)
    valid_actions['build_road'].trigger_action(controller.ws_client)
    for turn_i in range(6):
        controller.send_end_turn()
        controller.get_info_and_observation()
    print('Road')

    print(f"extras[EXTRA_MINE]: {build_tile['extras'][EXTRA_MINE]}")
    print(f"extras[EXTRA_ROAD]: {build_tile['extras'][EXTRA_ROAD]}")
    for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            print(
                f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')

    valid_actions = unit_opt.get_actions(138, valid_only=True)
    valid_actions['pillage'].trigger_action(controller.ws_client)
    for turn_i in range(1):
        controller.send_end_turn()
        controller.get_info_and_observation()
    print('Pillage')

    print(f"extras[EXTRA_MINE]: {build_tile['extras'][EXTRA_MINE]}")
    print(f"extras[EXTRA_ROAD]: {build_tile['extras'][EXTRA_ROAD]}")
    for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            print(
                f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')

    valid_actions = unit_opt.get_actions(138, valid_only=True)
    valid_actions['pillage'].trigger_action(controller.ws_client)
    # Wait for 15 turns (until the work is done)
    for turn_i in range(1):
        controller.send_end_turn()
        controller.get_info_and_observation()
    print('Pillage')

    print(f"extras[EXTRA_MINE]: {build_tile['extras'][EXTRA_MINE]}")
    print(f"extras[EXTRA_ROAD]: {build_tile['extras'][EXTRA_ROAD]}")
    for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            print(
                f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')
    print(f"Extra set bit: {find_set_bits(build_tile['extras'])}")
    # There is only a Gold extra in the tile and the pillage action should be invalid.
    assert (unit_focus.action_prob[map_const.DIR8_STAY][fc_types.ACTION_PILLAGE] == {'min': 0, 'max': 0})

    valid_actions = unit_opt.get_actions(138, valid_only=True)
    assert ('pillage' not in valid_actions)

    unit_focus = unit_opt.unit_data[137]
    ptile = unit_focus.ptile
    print(f"({ptile['x']}, {ptile['y']})")
    for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            print(
                f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')

    # NOTE: The following case shows that Mine pro is also inaccurate when the irrigation action is valid.
    unit_id = 139
    unit_focus = unit_opt.unit_data[unit_id]
    ptile = unit_focus.ptile
    print(f"Location: ({ptile['x']}, {ptile['y']})")
    for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            print(
                f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')
    # punit = unit_opt.unit_ctrl.units[unit_id]
    # unit_tile = unit_opt.map_ctrl.index_to_tile(punit['tile'])
    valid_actions = unit_opt.get_actions(unit_id, valid_only=True)
    valid_actions[f'goto_{map_const.DIR8_NORTH}'].trigger_action(controller.ws_client)
    print('Move north')

    controller.send_end_turn()
    controller.get_info_and_observation()
    print(unit_focus.action_prob)
    controller.get_info_and_observation()

    ptile = unit_focus.ptile
    print(f"Location: ({ptile['x']}, {ptile['y']})")
    print(ptile['extras'])
    for i in range(len(unit_focus.action_prob[map_const.DIR8_STAY])):
        if unit_focus.action_prob[map_const.DIR8_STAY][i] != {'min': 0, 'max': 0}:
            print(
                f'index: {i}, action name: {fc_types.ACTION_NAME_DICT[i]}, {unit_focus.action_prob[map_const.DIR8_STAY][i]}')


def main():
    controller = CivController(fc_args['username'])
    controller.set_parameter('debug.load_game', 'testcontroller_T27_2023-07-10-05_23')
    test_get_action_pro3(controller)


if __name__ == '__main__':
    main()
